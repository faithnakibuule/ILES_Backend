from django.urls import path
from . import views

urlpatterns = [
    path("student-stats/", views.student_stats, name = "student-stats"),
]
# dashboards/urls.py
from .views import DashboardStatsView

urlpatterns = [
    path('stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
]