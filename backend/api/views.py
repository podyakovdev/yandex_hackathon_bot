from rest_framework.viewsets import ModelViewSet
from survey.models import Survey, Question, Response
from survey.serializers import SurveySerializer, QuestionSerializer, ResponseSerializer


class SurveyViewSet(ModelViewSet):
    queryset = Survey.objects.all()
    serializer_class = SurveySerializer


class QuestionViewSet(ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer


class ResponseViewSet(ModelViewSet):
    queryset = Response.objects.all()
    serializer_class = ResponseSerializer
