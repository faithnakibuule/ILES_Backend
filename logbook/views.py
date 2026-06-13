from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django_filters.rest_framework import DjangoFilterBackend

from reviews.models import ReviewAction

from .filters import WeeklyLogFilter
from .models import WeeklyLog
from .permissions import IsWorkplaceSupervisor
from .serializers import (
    LogReadSerializer,
    LogReviewSerializer,
    LogWriteSerializer,
    StudentLogbookSummarySerializer,
    validate_required_log_fields,
)
from .services import (
    build_student_logbook_summary,
    can_transition,
    finalize_expired_logs,
    get_current_week_log,
)


class LogViewSet(viewsets.ModelViewSet):
    queryset = WeeklyLog.objects.all()
    serializer_class = LogReadSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = WeeklyLogFilter
    search_fields = ["intern__first_name", "intern__last_name", "intern__email"]
    ordering_fields = ["week_number", "status", "submitted_at"]

    def get_queryset(self):
        finalize_expired_logs()
        user = self.request.user
        base = (
            WeeklyLog.objects.select_related(
                "intern",
                "placement",
                "placement__workplace_supervisor",
            )
            .prefetch_related("evaluations", "review_actions")
            .order_by("week_number", "id")
        )

        if user.role == "admin":
            return base

        if user.role == "student":
            return base.filter(intern=user)

        if user.role == "workplace_supervisor":
            return base.filter(
                placement__workplace_supervisor=user,
                status__in=["SUBMITTED", "REVIEWED", "APPROVED"],
            )

        if user.role == "academic_supervisor":
            my_students = user.supervisor_students.all()
            return base.filter(intern__in=my_students, status__in=["REVIEWED", "APPROVED"])

        return WeeklyLog.objects.none()

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return LogWriteSerializer
        return LogReadSerializer

    def _serialize_read(self, instance, status_code=status.HTTP_200_OK):
        serializer = LogReadSerializer(instance, context=self.get_serializer_context())
        return Response(serializer.data, status=status_code)

    def create(self, request, *args, **kwargs):
        finalize_expired_logs()

        if request.user.role != "student":
            raise PermissionDenied("Only students can create weekly logs.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        placement, week_number, _ = get_current_week_log(request.user)
        if not placement:
            raise ValidationError("No active placement.")

        desired_status = request.data.get("status", "DRAFT")
        log = serializer.save(
            intern=request.user,
            placement=placement,
            week_number=week_number,
            status="DRAFT",
        )

        if desired_status == "SUBMITTED":
            validate_required_log_fields(log)
            if not can_transition(log, "SUBMITTED", request.user.role):
                raise ValidationError("You are not allowed to submit this weekly log.")
            from django.utils import timezone

            log.status = "SUBMITTED"
            log.submitted_at = timezone.localtime()
            log.save(update_fields=["status", "submitted_at"])

        headers = self.get_success_headers({})
        response = self._serialize_read(log, status_code=status.HTTP_201_CREATED)
        for key, value in headers.items():
            response[key] = value
        return response

    def partial_update(self, request, *args, **kwargs):
        finalize_expired_logs()
        instance = self.get_object()

        if request.user.role == "student" and instance.intern != request.user:
            raise PermissionDenied("You can only edit your own log.")

        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        log = serializer.save()

        if request.user.role == "student" and request.data.get("status") == "SUBMITTED":
            validate_required_log_fields(log)
            if not can_transition(log, "SUBMITTED", request.user.role):
                raise ValidationError("You are not allowed to submit this weekly log.")
            from django.utils import timezone

            log.status = "SUBMITTED"
            log.submitted_at = timezone.localtime()
            log.save(update_fields=["status", "submitted_at"])

        return self._serialize_read(log)

    def update(self, request, *args, **kwargs):
        finalize_expired_logs()
        instance = self.get_object()

        if request.user.role == "student" and instance.intern != request.user:
            raise PermissionDenied("You can only edit your own log.")

        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        log = serializer.save()

        if request.user.role == "student" and request.data.get("status") == "SUBMITTED":
            from .serializers import validate_required_log_fields
            validate_required_log_fields(log)
            if not can_transition(log, "SUBMITTED", request.user.role):
                raise ValidationError("You are not allowed to submit this weekly log.")
            from django.utils import timezone

            log.status = "SUBMITTED"
            log.submitted_at = timezone.localtime()
            log.save(update_fields=["status", "submitted_at"])

        return self._serialize_read(log)

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated], url_path="summary")
    def summary(self, request):
        finalize_expired_logs()

        if request.user.role != "student":
            raise PermissionDenied("Only students can view logbook summary.")

        serializer = StudentLogbookSummarySerializer(
            build_student_logbook_summary(request.user)
        )
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        finalize_expired_logs()
        log = self.get_object()

        if log.intern != request.user:
            raise PermissionDenied("You can only submit your own weekly log.")

        if log.status == "SUBMITTED":
            return Response({"message": "Log submitted successfully."})

        validate_required_log_fields(log)

        if can_transition(log, "SUBMITTED", request.user.role):
            from django.utils import timezone

            log.status = "SUBMITTED"
            log.submitted_at = timezone.localtime()
            log.save(update_fields=["status", "submitted_at"])
            return Response({"message": "Log submitted successfully."})

        raise ValidationError("You are not allowed to make this transition.")

    @action(
        detail=True,
        methods=["post"],
        permission_classes=[IsWorkplaceSupervisor],
        url_path="review",
    )
    def review_log(self, request, pk=None):
        log = self.get_object()

        if log.status != "SUBMITTED":
            raise ValidationError("Only submitted logs can be reviewed.")

        log.status = "REVIEWED"
        log.save(update_fields=["status"])
        comment = request.data.get("comment", request.data.get("review_comment", ""))

        ReviewAction.objects.create(
            log=log,
            action_by=request.user,
            action="APPROVED",
            comment=comment or "Log reviewed and approved",
        )
        return Response({"message": "Log approved and marked as REVIEWED."})

    @action(detail=True, methods=["post"], permission_classes=[IsWorkplaceSupervisor])
    def send_back(self, request, pk=None):
        log = self.get_object()

        if not can_transition(log, "DRAFT", request.user.role):
            raise ValidationError("You are not allowed to send this log back.")

        serializer = LogReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment = serializer.validated_data["review_comment"]

        ReviewAction.objects.create(
            log=log,
            action_by=request.user,
            action="SENT_BACK",
            comment=comment,
        )

        log.status = "DRAFT"
        log.submitted_at = None
        log.save(update_fields=["status", "submitted_at"])

        return Response(
            {
                "status": "log sent back",
                "message": "Log returned to student for revisions.",
                "comment": comment,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def approve(self, request, pk=None):
        log = self.get_object()

        if log.status != "REVIEWED":
            raise ValidationError("Only reviewed logs can be approved.")
        
        log.status = "APPROVED"
        log.save(update_fields=["status"])

        ReviewAction.objects.create(
            log=log,
            action_by=request.user,
            action="APPROVED",
            comment="Log officially approved",
        )
        return Response({"message": "Log status updated to APPROVED."})

