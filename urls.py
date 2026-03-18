from django.urls import path
from .views import WeeklyLogListView

urlpattersns = [
    path('logs/', WeeklyLogListView.as_view(), name='weekly-logs'),
]