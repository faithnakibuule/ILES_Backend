# logbook/serializers.py

from rest_framework import serializers
from .models import WeeklyLog

class LogReadSerializer(serializers.ModelSerializer):
    """ 
    Used for GET requests — rich display data including
    intern name and placement company.
    """

    # These fields cross model boundaries — they navigate
    # to related models using dot notation in 'source'

    intern_name = serializers.CharField(
        source='intern.get_full_name',  # calls get_full_name() on the related CustomUser
        read_only=True
    )
    placement_company = serializers.CharField(
        source='placement.company_name',  # reads company_name from InternshipPlacement
        read_only=True
    )
    overdue = serializers.BooleanField(source='is_overdue', read_only=True)

    latest_review_comment = serializers.SerializerMethodField()
    def get_latest_review_comment(self, obj):
        latest = obj.logbook_review_actions.first()
        if latest:
            return latest.comment
        return None

    class Meta:#Tells DRF which model to serialize and which fields to include
        model = WeeklyLog
        fields = [
            'id',
            'intern_name',          # from CustomUser (via source)
            'placement_company',    # from InternshipPlacement (via source)
            'week_number',
            'activities',
            'learning_points',
            'status',
            'submitted_at',
            'overdue',
        ]
        read_only_fields = fields   # nothing can be written through this serializer


class LogWriteSerializer(serializers.ModelSerializer):
    """
    Used for POST/PATCH requests — only the fields
    the intern is allowed to edit.
    """

    def validate_week_number(self, value):
        # DRF automatically calls validate_<field_name> before saving
        if value < 1 or value > 12:
            raise serializers.ValidationError(
                "Week number must be between 1 and 12."
            )
        return value  # always return value if valid — or data gets swallowed

    class Meta:
        model = WeeklyLog
        fields = [
            'week_number',
            'activities',
            'learning_points',
            'placement',
        ]
        # No read_only_fields — this serializer is meant for writing

class LogReviewSerializer(serializers.Serializer):
    """
    used when supervisor sends back a comment
    """
    review_comment = serializers.CharField(
        required=True,
        allow_blank=False,
        help_text="Comment from supervisor explaining the review decision."
    )