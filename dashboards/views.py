from django.db.models import Avg, Count, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from logbook.models import WeeklyLog
from logbook.serializers import LogReadSerializer
from logbook.services import (
    build_student_logbook_summary,
    get_active_placement,
    get_week_number_for_date,
)
from placements.models import Company, InternshipPlacement
from reviews.models import Evaluation, ReviewAction
from reviews.serializers import EvaluationSerializer, ReviewActionSerializer
from users.models import CustomUser
from users.permissions import IsAcademicSupervisor


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def student_stats(request):
    user = request.user
    if user.role != "student":
        return Response({"detail": "Only students can access this endpoint."}, status=403)

    qs = WeeklyLog.objects.filter(intern=user)
    logs_submitted = qs.filter(status__in=["SUBMITTED", "REVIEWED", "APPROVED"]).count()
    pending_review = qs.filter(status="SUBMITTED").count()
    approved_logs = qs.filter(status="APPROVED").count()
    overdue_logs = sum(1 for log in qs.exclude(status="APPROVED") if log.is_overdue)

    placement = get_active_placement(user)
    total_weeks = 0
    if placement:
        total_weeks = ((placement.end_date - placement.start_date).days // 7) + 1

    weeks_remaining = max(total_weeks - approved_logs, 0)

    return Response(
        {
            "logs_submitted": logs_submitted,
            "pending_review": pending_review,
            "approved_logs": approved_logs,
            "weeks_remaining": weeks_remaining,
            "overdue_logs": overdue_logs,
        }
    )


class AdminDashboardOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != "admin":
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        pending_evaluations = WeeklyLog.objects.filter(status="REVIEWED").count()
        return Response(
            {
                "total_students": CustomUser.objects.filter(role="student").count(),
                "active_internships": InternshipPlacement.objects.filter(status="ACTIVE").count(),
                "completed_internships": InternshipPlacement.objects.filter(status="COMPLETED").count(),
                "total_companies": Company.objects.count(),
                "pending_evaluations": pending_evaluations,
                "total_workplace_supervisors": CustomUser.objects.filter(
                    role="workplace_supervisor"
                ).count(),
            }
        )


class DashboardStatsView(AdminDashboardOverviewView):
    pass


class StudentDashboardOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != "student":
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        placement = get_active_placement(user) or (
            InternshipPlacement.objects.select_related(
                "workplace_supervisor",
                "academic_supervisor",
                "company",
            )
            .filter(student=user)
            .order_by("-start_date", "-id")
            .first()
        )

        logs = (
            WeeklyLog.objects.select_related("placement")
            .filter(intern=user)
            .order_by("-week_number", "-id")
        )
        recent_logs = logs[:3]
        summary = build_student_logbook_summary(user)

        total_weeks = 0
        weeks_completed = logs.filter(status="APPROVED").count()
        upcoming_deadlines = []
        if placement:
            total_weeks = ((placement.end_date - placement.start_date).days // 7) + 1
            if summary.get("current_week_deadline"):
                upcoming_deadlines.append(
                    {
                        "label": f"Week {summary.get('current_week')} log deadline",
                        "due_at": summary["current_week_deadline"],
                    }
                )

        return Response(
            {
                "placement": {
                    "id": placement.id,
                    "company": placement.company.name if placement and placement.company else placement.company_name if placement else None,
                    "status": placement.status if placement else None,
                    "start_date": placement.start_date if placement else None,
                    "end_date": placement.end_date if placement else None,
                    "workplace_supervisor_name": (
                        placement.workplace_supervisor.get_full_name() or placement.workplace_supervisor.email
                    )
                    if placement and placement.workplace_supervisor
                    else None,
                    "academic_supervisor_name": (
                        placement.academic_supervisor.get_full_name() or placement.academic_supervisor.email
                    )
                    if placement and placement.academic_supervisor
                    else None,
                }
                if placement
                else None,
                "recent_logs": LogReadSerializer(
                    recent_logs, many=True, context={"request": request}
                ).data,
                "progress": {
                    "weeks_completed": weeks_completed,
                    "total_weeks": total_weeks,
                    "current_week": summary.get("current_week"),
                },
                "upcoming_deadlines": upcoming_deadlines,
            }
        )


class WorkplaceStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        supervisor = request.user
        if supervisor.role != "workplace_supervisor":
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        today = timezone.localdate()
        pending_reviews = WeeklyLog.objects.filter(
            placement__workplace_supervisor=supervisor,
            status="SUBMITTED",
        ).count()
        reviewed_today = ReviewAction.objects.filter(
            action_by=supervisor,
            timestamp__date=today,
            action="APPROVED",
        ).count()
        total_interns = InternshipPlacement.objects.filter(
            workplace_supervisor=supervisor
        ).count()

        return Response(
            {
                "pending_reviews": pending_reviews,
                "approved_today": reviewed_today,
                "total_interns": total_interns,
            }
        )


class WorkplaceDashboardOverviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != "workplace_supervisor":
            return Response({"detail": "Forbidden"}, status=status.HTTP_403_FORBIDDEN)

        placements = (
            InternshipPlacement.objects.select_related("student", "company")
            .filter(workplace_supervisor=user)
            .order_by("student_id", "-start_date", "-id")
        )

        unique_placements = {}
        for placement in placements:
            if placement.student_id not in unique_placements:
                unique_placements[placement.student_id] = placement
        placements = unique_placements.values()

        pending_logs = (
            WeeklyLog.objects.select_related("intern", "placement")
            .filter(placement__workplace_supervisor=user, status="SUBMITTED")
            .order_by("-submitted_at", "-id")
        )
        recent_activity = ReviewAction.objects.filter(
            Q(log__placement__workplace_supervisor=user) | Q(action_by=user)
        ).select_related("action_by", "log")[:5]

        return Response(
            {
                "assigned_students": [
                    {
                        "id": placement.id,
                        "student_id": placement.student_id,
                        "name": placement.student.get_full_name() or placement.student.email,
                        "company": placement.company.name if placement.company else placement.company_name,
                        "status": placement.status,
                    }
                    for placement in placements
                ],
                "pending_logbook_approvals": {
                    "count": pending_logs.count(),
                    "logs": LogReadSerializer(
                        pending_logs[:5], many=True, context={"request": request}
                    ).data,
                },
                "recent_activity": ReviewActionSerializer(recent_activity, many=True).data,
            }
        )


class AcademicStatsView(APIView):
    permission_classes = [IsAuthenticated, IsAcademicSupervisor]

    def get(self, request):
        user = request.user
        logs_to_score = WeeklyLog.objects.filter(
            placement__academic_supervisor=user,
            status="REVIEWED",
        ).exclude(evaluations__academic_supervisor=user).count()

        avg_result = Evaluation.objects.filter(academic_supervisor=user).aggregate(
            avg=Avg("total_score")
        )
        fully_approved = WeeklyLog.objects.filter(
            placement__academic_supervisor=user,
            status="APPROVED",
        ).count()

        return Response(
            {
                "logs_to_score": logs_to_score,
                "avg_cohort_score": round(avg_result["avg"] or 0, 1),
                "fully_approved": fully_approved,
            }
        )


class AcademicDashboardOverviewView(APIView):
    permission_classes = [IsAuthenticated, IsAcademicSupervisor]

    def get(self, request):
        user = request.user
        placements = (
            InternshipPlacement.objects.select_related("student", "company")
            .filter(academic_supervisor=user)
            .order_by("student_id", "-start_date", "-id")
        )
        pending_count = WeeklyLog.objects.filter(
            placement__academic_supervisor=user,
            status="REVIEWED",
        ).exclude(evaluations__academic_supervisor=user).count()

        unique_placements = {}
        for placement in placements:
            if placement.student_id not in unique_placements:
                unique_placements[placement.student_id] = placement
        placements = unique_placements.values()

        students = []
        for placement in placements:
            student_logs = WeeklyLog.objects.filter(
                placement=placement, intern=placement.student
            )
            avg_score = (
                Evaluation.objects.filter(
                    log__placement=placement,
                    log__intern=placement.student,
                ).aggregate(avg=Avg("total_score"))["avg"]
                or 0
            )
            students.append(
                {
                    "id": placement.id,
                    "student_id": placement.student_id,
                    "name": placement.student.get_full_name() or placement.student.email,
                    "company": placement.company.name if placement.company else placement.company_name,
                    "status": placement.status,
                    "logs_submitted": student_logs.exclude(status="DRAFT").count(),
                    "avg_score": round(avg_score, 1) if avg_score else None,
                }
            )

        return Response(
            {
                "assigned_students": students,
                "pending_evaluations": pending_count,
                "quick_links": [{"label": "Go to Evaluations", "path": "/academic/evaluations"}],
            }
        )


class StudentProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id=None):
        if student_id is None:
            student_id = request.user.id

        student = get_object_or_404(CustomUser, id=student_id, role="student")
        if request.user.role == "student" and request.user.id != student.id:
            return Response({"error": "Forbidden"}, status=403)

        logs = (
            WeeklyLog.objects.prefetch_related("evaluations")
            .filter(intern=student)
            .order_by("week_number")
        )

        progress_data = []
        for log in logs:
            evaluation = log.evaluations.first() if log.status == "APPROVED" else None
            progress_data.append(
                {
                    "week_number": log.week_number,
                    "status": log.status,
                    "score_if_approved": float(evaluation.total_score) if evaluation else None,
                }
            )

        return Response(progress_data)


class PendingLogsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        queryset = (
            WeeklyLog.objects.select_related("intern", "placement", "placement__workplace_supervisor")
            .filter(
                placement__workplace_supervisor=request.user,
                status="SUBMITTED",
            )
            .order_by("-submitted_at")
        )
        serializer = LogReadSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)


class LogsPerWeekView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = (
            WeeklyLog.objects.values("week_number")
            .annotate(count=Count("id"))
            .order_by("week_number")
        )
        return Response(list(data))


class StatusDistributionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = (
            WeeklyLog.objects.values("status")
            .annotate(count=Count("id"))
            .order_by("status")
        )
        return Response(list(data))


class CohortScoresView(APIView):
    permission_classes = [IsAuthenticated, IsAcademicSupervisor]

    def get(self, request):
        user = request.user
        placements = (
            InternshipPlacement.objects.select_related("student")
            .filter(academic_supervisor=user)
            .order_by("student_id", "-start_date", "-id")
        )

        unique_placements = {}
        for placement in placements:
            if placement.student_id not in unique_placements:
                unique_placements[placement.student_id] = placement
        placements = unique_placements.values()

        cohort_data = []
        for placement in placements:
            student_logs = WeeklyLog.objects.filter(
                placement=placement,
                intern=placement.student,
            )
            total_logs = student_logs.count()
            approved_logs = student_logs.filter(status="APPROVED").count()
            avg_score = (
                Evaluation.objects.filter(
                    log__placement=placement,
                    log__intern=placement.student,
                ).aggregate(avg=Avg("total_score"))["avg"]
                or 0
            )

            cohort_data.append(
                {
                    "id": placement.id,
                    "student_name": placement.student.get_full_name() or placement.student.email,
                    "company": placement.company.name if placement.company else placement.company_name,
                    "avg_score": round(avg_score, 2) if avg_score else 0,
                    "approved_logs": approved_logs,
                    "total_logs": total_logs,
                    "status": placement.status,
                }
            )

        cohort_data.sort(key=lambda item: item["avg_score"], reverse=True)
        return Response(cohort_data)


class WorkplaceInternDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, placement_id):
        placement = get_object_or_404(
            InternshipPlacement.objects.select_related(
                "student",
                "company",
                "workplace_supervisor",
                "academic_supervisor",
            ),
            id=placement_id,
            workplace_supervisor=request.user,
        )

        logs = WeeklyLog.objects.filter(placement=placement).order_by("week_number")
        history = ReviewAction.objects.filter(log__placement=placement).select_related("action_by")

        return Response(
            {
                "id": placement.id,
                "name": placement.student.get_full_name() or placement.student.email,
                "email": placement.student.email,
                "phone": placement.student.phone,
                "placement": {
                    "company_name": placement.company.name if placement.company else placement.company_name,
                    "start_date": placement.start_date,
                    "end_date": placement.end_date,
                    "status": placement.status,
                },
                "logs": LogReadSerializer(logs, many=True, context={"request": request}).data,
                "review_history": ReviewActionSerializer(history, many=True).data,
            }
        )
