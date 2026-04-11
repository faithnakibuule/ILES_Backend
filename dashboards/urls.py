from django.urls import path
from . import views
from .views import DashboardStatsView
from .views import WorkplaceStatsView
from .views import PendingLogsView
from .views import StudentProgressView

urlpatterns = [
    path("student-stats/", views.student_stats, name = "student-stats"),
    path("admin-stats/", DashboardStatsView.as_view(), name = "admin-stats"),
    path("workplace-stats/", WorkplaceStatsView.as_view(), name = 'workplace-stats'),
    path("pending-logs/", PendingLogsView.as_view(), name = 'pending-logs'),
    path(
        'student-progress/<int:student_id>/',
        StudentProgressView.as_view(),
        name='student-progress'
    ),
]
