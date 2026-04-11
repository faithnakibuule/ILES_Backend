
from django.shortcuts import render

# Create your views here.

# dashboards/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from rest_framework import status
from django.shortcuts import get_object_or_404
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
            placement__workplace_supervisor=supervisor,
            status = 'REVIEWED',
            submitted_at__date = today
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
class PendingLogsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        supervisor = request.user

        pending_logs = WeeklyLog.objects.filter(
            placement__workplace_supervisor=supervisor,
            status='SUBMITTED'
        ).select_related('intern', 'placement').order_by('-submitted_at')

        data = [
            {
                'id': log.id,
                'intern_name': f"{log.intern.first_name} {log.intern.last_name}",
                'week_number': log.week_number,
                'submitted_at': log.submitted_at,
                'status': log.status,
            }
            for log in pending_logs
        ]

        return Response(data)  

# iles_backend/dashboards/views.py


# ── StudentProgressView ───────────────────────────────────────────────────────
class StudentProgressView(APIView):
    """
    GET /api/dashboards/student-progress/{student_id}/

    Returns all weekly logs for a student with their week number,
    status, and score (if the log has been approved and evaluated).

    Used by: Student's own progress line chart, Academic supervisor view.
    Accessible by: The student themselves, academic supervisors, admins.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id):
        try:
            from logbook.models import WeeklyLog
            from users.models import CustomUser

            # Confirm the student exists
            student = get_object_or_404(CustomUser, id=student_id, role='student')

            # Security check: students can only see their OWN progress
            # Academic supervisors and admins can see anyone's
            user = request.user
            is_student_viewing_own = (
                user.role == 'student' and user.id == student.id
            )
            is_privileged = user.role in [
                'academic_supervisor', 'admin'
            ]

            if not is_student_viewing_own and not is_privileged:
                return Response(
                    {'error': 'You do not have permission to view this student\'s progress.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Fetch all logs for this student, ordered by week
            logs = WeeklyLog.objects.filter(
                intern=student
            ).order_by('week_number')

            # Build the response list
            progress_data = []
            for log in logs:
                # Try to get the evaluation score if this log was approved
                score = None
                if log.status == 'APPROVED':
                    try:
                        from reviews.models import Evaluation
                        evaluation = Evaluation.objects.filter(log=log).first()
                        if evaluation:
                            score = float(evaluation.total_score)
                    except Exception:
                        score = None

                progress_data.append({
                    'week_number': log.week_number,
                    'status': log.status,
                    'score_if_approved': score,
                })

            return Response(progress_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )