from django.urls import path
from users.views import WeeklyLogListView

urlpatterns = [
    path('logs/', WeeklyLogListView.as_view(), name='weekly-logs'),
]