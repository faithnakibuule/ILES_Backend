from django.urls import path
from . import views
from .views import DashboardStatsView

urlpatterns = [
    path("student-stats/", views.student_stats, name = "student-stats"),
    path("admin-stats/", DashboardStatsView.as_view(), name = "admin-stats"),
]
