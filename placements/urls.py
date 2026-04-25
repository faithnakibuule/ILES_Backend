from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import test_api
from .views import PlacementViewSet

router = DefaultRouter()
router.register(r'', PlacementViewSet, basename='placement')# One line generates all 5 CRUD endpoints automatically


urlpatterns = [
    path('', include(router.urls)),
    path("test/", test_api, name="test_api"),
]