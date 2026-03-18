from django.urls import path
from . import views

urlpatterns = [
    path("student-stats/", views.student_stats, name = "student-stats"),
]