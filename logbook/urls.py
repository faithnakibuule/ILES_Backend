from django.urls import path, include 
from rest_framework.routers import DefaultRouter
from .views import LogViewSet
from reviews.views import ReviewHistoryView

router = DefaultRouter()
router.register(r'logs', LogViewSet, basename='log')


urlpatterns = [
    path('', include(router.urls)),
    path('logs/<int:log_id>/history/', ReviewHistoryView.as_view(), name='log_review_history'),
]