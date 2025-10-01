from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SurveyViewSet, UserViewSet


router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")
router.register(r"surveys", SurveyViewSet, basename="surveys")


urlpatterns = [
    path("api/", include(router.urls)),
]


