import os
import asyncio

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from .models import User, Survey, SurveyResponse
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    SurveyImportSerializer,
    SurveyImportResultSerializer,
    SurveyResponseSerializer,
    SurveyResponseResultSerializer,
)


@method_decorator(csrf_exempt, name='dispatch')
class UserViewSet(viewsets.ViewSet):
    """
    ViewSet для регистрации и управления пользователями.
    """

    @action(detail=False, methods=["post"], url_path="register")
    def register_user(self, request):
        """
        POST /api/users/register
        Регистрация нового пользователя.
        """
        serializer = UserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = serializer.save()
            return Response(
                UserSerializer(user).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"detail": f"Ошибка при создании пользователя: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=False, methods=["get"], url_path="by-nickname/(?P<nickname>[^/.]+)")
    def get_by_nickname(self, request, nickname=None):
        """
        GET /api/users/by-nickname/<nickname>
        Получить пользователя по Telegram nickname.
        """
        try:
            user = User.objects.get(tg_nickname=nickname)
            return Response(UserSerializer(user).data)
        except User.DoesNotExist:
            return Response(
                {"detail": "Пользователь не найден"},
                status=status.HTTP_404_NOT_FOUND,
            )


@method_decorator(csrf_exempt, name='dispatch')
class SurveyViewSet(viewsets.ViewSet):
    """
    ViewSet для импорта опросов и приёма ответов.
    """

    @action(detail=False, methods=["post"], url_path="import")
    def import_survey(self, request):
        """
        POST /api/surveys/import
        Принимает external_id (id формы в Яндекс), опционально метаданные и список вопросов,
        сохраняет в БД и возвращает номер опроса (id).
        """
        serializer = SurveyImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        external_id = data["external_id"]

        try:
            from .yandex_forms import get_survey_from_yandex
        except Exception:
            get_survey_from_yandex = None

        client_id = os.environ.get("YANDEX_CLIENT_ID", "").strip()
        client_secret = os.environ.get("YANDEX_CLIENT_SECRET", "").strip()

        if not (get_survey_from_yandex and client_id and client_secret):
            return Response(
                {"detail": "Интеграция с Яндекс Формами не настроена."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        try:
            survey_data = asyncio.run(
                get_survey_from_yandex(external_id, client_id, client_secret)
            )
        except Exception as e:
            return Response(
                {"detail": f"Ошибка при запросе к Яндекс Формам: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        if not survey_data:
            return Response(
                {"detail": "Не удалось получить анкету из Яндекс Форм. Проверьте external_id и настройки API."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        title = survey_data.get("title") or f"Опрос {external_id}"
        description = survey_data.get("description", "")
        questions = survey_data.get("questions") or []

        if not questions:
            return Response(
                {"detail": "Анкета из Яндекс Форм не содержит вопросов."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        survey = Survey.objects.create(
            external_id=external_id,
            title=title,
            description=description,
            questions=questions,
        )

        return Response(
            SurveyImportResultSerializer(survey).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"], url_path="test-yandex")
    def test_yandex_connection(self, request):
        """
        GET /api/surveys/test-yandex
        Тестирует подключение к Яндекс Формам
        """
        try:
            from .yandex_forms import get_survey_from_yandex
        except Exception as e:
            return Response(
                {"detail": f"Ошибка импорта модуля: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        client_id = os.environ.get("YANDEX_CLIENT_ID", "").strip()
        client_secret = os.environ.get("YANDEX_CLIENT_SECRET", "").strip()

        if not client_id or not client_secret:
            return Response(
                {"detail": "YANDEX_CLIENT_ID или YANDEX_CLIENT_SECRET не установлены"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Тестируем с тестовым ID
        test_id = "test_form_id"
        try:
            result = asyncio.run(
                get_survey_from_yandex(test_id, client_id, client_secret)
            )
            return Response({
                "client_id": client_id,
                "client_secret": client_secret[:10] + "...",
                "test_result": result,
                "message": "Подключение к API работает" if result is None else "Получены данные"
            })
        except Exception as e:
            return Response(
                {"detail": f"Ошибка при тестировании API: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["post"], url_path="submit")
    def submit_answers(self, request, pk=None):
        """
        POST /api/surveys/<id>/submit
        Принимает ответы пользователя и сохраняет их. Возвращает сохранённый объект.
        Тут надо дописать отправку ответов в Яндекс Формы.
        """
        try:
            survey = Survey.objects.get(pk=pk)
        except Survey.DoesNotExist:
            return Response({"detail": "Survey not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = SurveyResponseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Найти пользователя по ID если передан
        user = None
        if data.get("user_id"):
            try:
                user = User.objects.get(id=data["user_id"])
            except User.DoesNotExist:
                pass

        response = SurveyResponse.objects.create(
            survey=survey,
            user=user,
            answers=data["answers"],
            telegram_user_id=data.get("telegram_user_id", ""),
            telegram_username=data.get("telegram_username", ""),
        )

        # Отправка в Яндекс Формы:
        #########################################################


        return Response(
            SurveyResponseResultSerializer(response).data,
            status=status.HTTP_201_CREATED,
        )
