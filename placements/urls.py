from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlacementViewSet

router = DefaultRouter()

# One line generates all 5 CRUD endpoints automatically
# basename required because we use custom get_queryset
router.register(r'', PlacementViewSet, basename='placement')

urlpatterns = [
    path('', include(router.urls)),
]