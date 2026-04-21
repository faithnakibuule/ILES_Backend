from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, EvaluationViewSet, ReviewHistoryView, CriteriaViewSet

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'evaluations', EvaluationViewSet, basename='evaluation')
router.register(r'criteria', CriteriaViewSet, basename='criteria')

urlpatterns = [
    path('', include(router.urls)),
    path('logs/<int:log_id>/history/', ReviewHistoryView.as_view(), name='log-history'),
]
