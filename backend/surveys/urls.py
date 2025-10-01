from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, SurveyViewSet


router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")
router.register(r"surveys", SurveyViewSet, basename="surveys")


urlpatterns = [
    path("api/", include(router.urls)),
]


