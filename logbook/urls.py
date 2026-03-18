from django.urls import path
from .views import WeeklyLogListView

urlpatterns = [
    path('logs/', WeeklyLogListView.as_view(), name='weekly-logs')
]