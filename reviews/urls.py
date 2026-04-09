from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, EvaluationViewSet

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'evaluations', EvaluationViewSet, basename='evaluation')

urlpatterns = router.urls