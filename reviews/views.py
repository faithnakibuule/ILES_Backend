from django.db.models import Q

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from django_filters.rest_framework import DjangoFilterBackend

from logbook.models import WeeklyLog

from .models import Evaluation, EvaluationCriteria, Notification, ReviewAction
from .serializers import (
    EvaluationCriteriaSerializer,
    EvaluationSerializer,
    NotificationSerializer,
    ReviewActionSerializer,
)


class ReviewHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, log_id):
        try:
            log = WeeklyLog.objects.get(id=log_id)
        except WeeklyLog.DoesNotExist:
            return Response({"error": "Log not found."}, status=404)

        user = request.user
        if user.role == "student" and log.intern != user:
            raise PermissionDenied("You can only view your own review history.")
        if (
            user.role == "workplace_supervisor"
            and log.placement.workplace_supervisor != user
        ):
            raise PermissionDenied("You can only view review history for your interns.")
        if (
            user.role == "academic_supervisor"
            and log.placement.academic_supervisor != user
        ):
            raise PermissionDenied("You can only view review history for your students.")

        actions = log.review_actions.all().order_by("-timestamp")
        serializer = ReviewActionSerializer(actions, many=True)
        return Response(serializer.data)


class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["is_read", "notification_type"]

    def get_queryset(self):
        return (
            Notification.objects.select_related("recipient")
            .filter(recipient=self.request.user)
            .order_by("-created_at")
        )

    @action(detail=True, methods=["patch"])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=["is_read"])
        return Response({"status": "marked as read"})

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response({"status": "all notifications marked as read"})


class EvaluationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = EvaluationSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["log", "log__status"]

    def get_queryset(self):
        user = self.request.user
        base = Evaluation.objects.select_related(
            "log",
            "log__intern",
            "log__placement",
            "academic_supervisor",
        )

        if user.role == "academic_supervisor":
            return base.filter(
                Q(academic_supervisor=user)
                | Q(log__placement__academic_supervisor=user)
            ).distinct()

        if user.role == "student":
            return base.filter(log__intern=user)

        if user.role == "workplace_supervisor":
            return base.filter(log__placement__workplace_supervisor=user)

        if user.role == "admin":
            return base

        return Evaluation.objects.none()

    def _validate_log_access(self, user, log):
        if log.status == "APPROVED":
            if not Evaluation.objects.filter(log=log, academic_supervisor=user).exists():
                raise ValidationError("This log is already approved and cannot be scored again.")
        elif log.status != "REVIEWED":
            raise ValidationError(
                f"Log must be REVIEWED before evaluation. Current status: {log.status}"
            )

        if user.role != "academic_supervisor":
            raise PermissionDenied("Only academic supervisors can create evaluations.")

        placement = getattr(log, "placement", None)
        if placement and placement.academic_supervisor_id and placement.academic_supervisor != user:
            raise PermissionDenied("You can only evaluate students assigned to you.")

    def create(self, request, *args, **kwargs):
        user = request.user
        log_id = request.data.get("log")

        try:
            log = WeeklyLog.objects.select_related("placement").get(id=log_id)
        except WeeklyLog.DoesNotExist:
            raise ValidationError("Log not found.")

        self._validate_log_access(user, log)

        existing = Evaluation.objects.filter(log=log, academic_supervisor=user).first()
        if existing:
            partial = self.get_serializer(existing, data=request.data, partial=True)
            partial.is_valid(raise_exception=True)
            partial.save()
            return Response(partial.data, status=status.HTTP_200_OK)

        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        user = self.request.user
        log_id = self.request.data.get("log")

        try:
            log = WeeklyLog.objects.select_related("placement").get(id=log_id)
        except WeeklyLog.DoesNotExist:
            raise ValidationError("Log not found.")

        self._validate_log_access(user, log)

        evaluation = serializer.save(academic_supervisor=user)
        if log.status != "APPROVED":
            log.status = "APPROVED"
            log.save(update_fields=["status"])

        ReviewAction.objects.create(
            log=log,
            action_by=user,
            action="SCORED",
            comment=evaluation.comments or "Academic evaluation submitted.",
        )

    def perform_update(self, serializer):
        evaluation = self.get_object()
        user = self.request.user

        if user.role != "academic_supervisor" or evaluation.academic_supervisor != user:
            raise PermissionDenied("You can only edit your own evaluations.")

        serializer.save()

    @action(detail=False, methods=["get"])
    def pending(self, request):
        user = request.user
        if user.role != "academic_supervisor":
            raise PermissionDenied("Only academic supervisors can access pending evaluations.")

        queryset = (
            WeeklyLog.objects.select_related("intern", "placement")
            .filter(
                placement__academic_supervisor=user,
                status__in=["REVIEWED", "APPROVED"],
            )
            .order_by("-submitted_at", "-id")
        )

        rows = []
        for log in queryset:
            evaluation = log.evaluations.filter(academic_supervisor=user).first()
            rows.append(
                {
                    "log_id": log.id,
                    "student_name": log.intern.get_full_name() or log.intern.email,
                    "week_number": log.week_number,
                    "company": log.placement.company_name,
                    "review_date": log.submitted_at,
                    "status": log.status,
                    "evaluation": EvaluationSerializer(evaluation).data if evaluation else None,
                    "activities": log.activities,
                    "learning_points": log.learning_points,
                    "supervisor_comment": getattr(log, "supervisor_comment", "") or "",
                }
            )

        return Response(rows)


class CriteriaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EvaluationCriteria.objects.all().order_by("id")
    serializer_class = EvaluationCriteriaSerializer
    permission_classes = [IsAuthenticated]

