<<<<<<< HEAD
<<<<<<< HEAD
from django.shortcuts import render

# Create your views here.
=======
# dashboards/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
=======
from rest_framework.decorators import api_view, permission_classes
>>>>>>> 0edc1e4afaf9f39aa7169e23309b43ad83b0573f
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from  logbook.models import WeeklyLog
from users.models import CustomUser
from placements.models import InternshipPlacement

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_stats(request):
    user = request.user

    if getattr(user, "role", None) != "student":
        return Response ({"detail": "Only students can access this endpoint."}, status = 403)
    
    qs = WeeklyLog.objects.filter(intern = user)

    logs_submitted = qs.filter(status__in = ["SUBMITTED", "APPROVED"]).count()
    pending_review = qs.filter(status = "SUBMITTED").count()
    approved_logs = qs.filter(status = "APPROVED").count()
    weeks_remaining = max(12 - approved_logs, 0)
    overdue_logs = sum(1 for log in qs.exclude(status = "APPROVED") if log.is_overdue())

    return Response({
        "logs_submitted": logs_submitted,
        "pending_review": pending_review,
        "approved_logs": approved_logs,
        "weeks_remaining": weeks_remaining,
        "overdue_logs": overdue_logs,
    })
# dashboards/views.py
class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total_students = CustomUser.objects.filter(
            role='student'
        ).count()

        active_placements = InternshipPlacement.objects.filter(
            status='ACTIVE'
        ).count()

        return Response({
            'total_students':    total_students,
            'active_placements': active_placements,
        })
<<<<<<< HEAD
>>>>>>> f9129086cb0de8063b216baf636a138669a32341
=======
>>>>>>> 0edc1e4afaf9f39aa7169e23309b43ad83b0573f
