from django.urls import path
from . import views
from .views import DashboardStatsView
from .views import WorkplaceStatsView
from .views import AcademicStatsView

urlpatterns = [
    path("student-stats/", views.student_stats, name = "student-stats"),
    path("admin-stats/", DashboardStatsView.as_view(), name = "admin-stats"),
    path("workplace-stats/", WorkplaceStatsView.as_view(), name = 'workplace-stats'),
    path("academic-stats/", AcademicStatsView.as_view(), name = 'academic-stats'),
]
