
from django.shortcuts import render
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
from django.db.models import Avg, Count
from reviews.models import Evaluation
from users.permissions import IsAcademicSupervisor
from rest_framework.generics import ListAPIView
from logbook.serializers import LogReadSerializer
from django.db.models import Avg, Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from placements.models import InternshipPlacement
from logbook.models import WeeklyLog

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

class AcademicStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAcademicSupervisor]

    def get(self, request):
        user = request.user
        reviewed_log_ids = WeeklyLog.objects.filter(
            status = 'REVIEWED'
        ).values_list('id', flat = True)

        already_scored_log_ids = Evaluation.objects.filter(
            log_id__in = reviewed_log_ids,
            academic_supervisor = user
        ).values_list('log_id', flat = True)

        logs_to_score = WeeklyLog.objects.filter(
            status = 'REVIEWED'
        ).exclude(id__in = already_scored_log_ids
        ).count()

        avg_result = Evaluation.objects.filter(
            academic_supervisor = user
        ).aggregate(avg = Avg('total_score'))
        avg_cohort_score = round(avg_result['avg'] or 0, 1)

        fully_approved = WeeklyLog.objects.filter(
            status = 'APPROVED'
        ).count()

        return Response({
            'logs_to_score': logs_to_score,
            'avg_cohort_score': avg_cohort_score,
            'fully_approved': fully_approved,
        })
# iles_backend/dashboards/views.py


# ── StudentProgressView ───────────────────────────────────────────────────────
class StudentProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id=None):
        # If /me/ route — use the logged-in user themselves
        if student_id is None:
            student_id = request.user.id

        student = get_object_or_404(CustomUser, id=student_id, role='student')

        # Security: students can only see their own
        if request.user.role == 'student' and request.user.id != student.id:
            return Response({'error': 'Forbidden'}, status=403)

        logs = (
            WeeklyLog.objects
            .prefetch_related('evaluations')
            .filter(intern=student)
            .order_by('week_number')
        )

        progress_data = []
        for log in logs:
            score = None
            if log.status == 'APPROVED':
                evaluation = log.evaluations.first()
                if evaluation:
                    score = float(evaluation.total_score)
            progress_data.append({
                'week_number': log.week_number,
                'status': log.status,
                'score_if_approved': score,
            })

        return Response(progress_data)
        
class PendingLogsView(ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogReadSerializer
    def get_queryset(self):
        return(
            WeeklyLog.objects
            .select_related('intern', 'placement', 'placement__workplace_supervisor')
            .filter(
            placement__workplace_supervisor = self.request.user,
            status = 'SUBMITTED'
            )
            .order_by('-submitted_at')
        )
    
class LogsPerWeekView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = (
            WeeklyLog.objects
            .values('week_number')
            .annotate(count = Count('id'))
            .order_by('week_number')
        )
        return Response(list(data))

class StatusDistributionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = (
            WeeklyLog.objects
            .values('status')
            .annotate(count=Count('id'))
            .order_by('status')
        )
        return Response(list(data))
    
        
class CohortScoresView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        placements = (
            InternshipPlacement.objects
            .filter(academic_supervisor=user)
            .select_related('student')
            .prefetch_related('student__weeklyLogs__evaluations')
        )

        cohort_data = []

        for placement in placements:
            student = placement.student

            all_logs = student.weeklyLogs.all()
            total_logs = len(all_logs)
            approved_logs = sum(1 for l in all_logs if l.status == 'APPROVED')

            scores = [
                float(e.total_score)
                for l in all_logs if l.status == 'APPROVED'
                for e in l.evaluations.all()
                if e.total_score is not None
            ]

            avg_score = round(sum(scores) / len(scores), 2) if scores else 0

            cohort_data.append({
                'student_name': f"{student.first_name} {student.last_name}".strip(),
                'avg_score':    avg_score,
                'approved_logs': approved_logs,
                'total_logs':    total_logs,
            })

        cohort_data.sort(key=lambda x: x['avg_score'], reverse=True)

        return Response(cohort_data)        
