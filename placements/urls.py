from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlacementViewSet

router = DefaultRouter()
router.register(r'', PlacementViewSet, basename='placement')# One line generates all 5 CRUD endpoints automatically


urlpatterns = [
    path('', include(router.urls)),
]