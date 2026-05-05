from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import test_api
from .views import PlacementViewSet, CompanyViewSet

router = DefaultRouter()
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'', PlacementViewSet, basename='placement')


urlpatterns = [
    path('', include(router.urls)),
    path("test/", test_api, name="test_api"),
]