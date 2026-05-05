from rest_framework.routers import DefaultRouter, path
from .views import AdminUserViewSet,ExportPlacementsView, ExportLogsView
from django.urls import path

# Router generates all CRUD URLs for AdminUserViewSet
router = DefaultRouter()
router.register(r'users', AdminUserViewSet, basename='admin-users')

urlpatterns = [
    path('export/placements/', ExportPlacementsView.as_view(), name='export-placements'),
    path('export/logs/', ExportLogsView.as_view(), name='export-logs'),
]

urlpatterns += router.urls