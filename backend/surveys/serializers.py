from rest_framework import serializers

from .models import User, Survey, SurveyResponse


class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['tg_nickname', 'name', 'surname', 'age', 'gender']


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'tg_nickname', 'name', 'surname', 'age', 'gender', 'created_at']


class SurveyImportSerializer(serializers.Serializer):
    # Бекенд работает только с Яндекс Формами — принимаем только external_id
    external_id = serializers.CharField()


class SurveyImportResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Survey
        fields = ["id", "external_id", "title", "description", "questions"]


class SurveyResponseSerializer(serializers.Serializer):
    answers = serializers.ListField(child=serializers.CharField(), allow_empty=False)
    user_id = serializers.IntegerField(required=False, help_text="ID пользователя из базы")
    telegram_user_id = serializers.CharField(required=False, allow_blank=True)
    telegram_username = serializers.CharField(required=False, allow_blank=True)


class SurveyResponseResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyResponse
        fields = ["id", "survey", "answers", "user", "telegram_user_id", "telegram_username", "submitted_at"]


