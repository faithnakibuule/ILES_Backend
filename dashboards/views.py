from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone

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
    overdue_logs = sum(1 for log in qs.exclude(status = "APPROVED") if log.is_overdue)

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

class WorkplaceStatsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        supervisor = request.user
        today = timezone.now().date()

        pending_reviews = WeeklyLog.objects.filter(
            placement__workplace_supervisor=supervisor,
            status = 'SUBMITTED'
        ).count()

        approved_today = WeeklyLog.objects.filter(
            placement__workplace_supervisor = supervisor,
            status = 'REVIEWED',
            updated_at__date = today
        ).count()

        total_interns = InternshipPlacement.objects.filter(
            workplace_supervisor = supervisor,
            status = 'ACTIVE'
        ).count()

        return Response({
            'pending_reviews': pending_reviews,
            'approved_today': approved_today,
            'total_interns': total_interns,
        })
    
