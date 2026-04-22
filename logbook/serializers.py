# logbook/serializers.py

from rest_framework import serializers

from .models import WeeklyLog
from .services import (
    REQUIRED_LOG_FIELDS,
    get_active_placement,
    get_current_week_log,
    student_can_edit_log,
)


class LogReadSerializer(serializers.ModelSerializer):
    intern_name = serializers.CharField(source="intern.get_full_name", read_only=True)
    placement_company = serializers.CharField(
        source="placement.company_name",
        read_only=True,
    )
    overdue = serializers.BooleanField(source="is_overdue", read_only=True)
    latest_review_comment = serializers.SerializerMethodField()
    deadline_at = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()

    def get_latest_review_comment(self, obj):
        latest = obj.review_actions.first()
        if latest:
            return latest.comment
        return None

    def get_deadline_at(self, obj):
        from .services import get_week_deadline

        return get_week_deadline(obj.placement, obj.week_number)

    def get_can_edit(self, obj):
        request = self.context.get("request")
        if not request or request.user.role != "student":
            return False
        return student_can_edit_log(obj)

    class Meta:
        model = WeeklyLog
        fields = [
            "id",
            "intern_name",
            "placement",
            "placement_company",
            "week_number",
            "activities",
            "learning_points",
            "status",
            "submitted_at",
            "deadline_at",
            "overdue",
            "can_edit",
            "latest_review_comment",
        ]
        read_only_fields = fields


class LogWriteSerializer(serializers.ModelSerializer):
    activities = serializers.CharField(required=False, allow_blank=True)
    learning_points = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = WeeklyLog
        fields = [
            "activities",
            "learning_points",
        ]

    def validate(self, attrs):
        request = self.context.get("request")
        user = getattr(request, "user", None)

        if self.instance:
            if self.instance.intern != user:
                raise serializers.ValidationError("You can only edit your own log.")
            if not student_can_edit_log(self.instance):
                raise serializers.ValidationError(
                    "This week's log is closed and can no longer be edited."
                )
            return attrs

        if not user or user.role != "student":
            return attrs

        placement = get_active_placement(user)
        if not placement:
            raise serializers.ValidationError("No active placement.")

        _, week_number, current_log = get_current_week_log(user)
        if current_log:
            raise serializers.ValidationError(
                {"week_number": f"You already have a log for week {week_number}."}
            )

        return attrs


class LogReviewSerializer(serializers.Serializer):
    review_comment = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text="Comment from supervisor explaining the review decision.",
    )


class StudentLogbookSummarySerializer(serializers.Serializer):
    has_active_placement = serializers.BooleanField()
    placement = serializers.SerializerMethodField()
    current_week = serializers.IntegerField(allow_null=True)
    current_log_id = serializers.IntegerField(allow_null=True)
    current_week_deadline = serializers.DateTimeField(allow_null=True)
    missed_weeks = serializers.ListField(child=serializers.IntegerField())

    def get_placement(self, obj):
        placement = obj.get("placement")
        if not placement:
            return None

        return {
            "id": placement.id,
            "company_name": placement.company_name,
            "start_date": placement.start_date,
            "end_date": placement.end_date,
            "status": placement.status,
        }

def validate_required_log_fields(log):
    missing_fields = [
        field for field in REQUIRED_LOG_FIELDS if not (getattr(log, field) or "").strip()
    ]
    if missing_fields:
        raise serializers.ValidationError(
            {
                "detail": (
                    "Complete all required fields before submitting a weekly log."
                ),
                "missing_fields": missing_fields,
            }
        )
