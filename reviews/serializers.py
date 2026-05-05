from rest_framework import serializers

from .models import Evaluation, EvaluationCriteria, Notification, ReviewAction


class EvaluationCriteriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationCriteria
        fields = ["id", "name", "description", "max_score", "weight"]


class EvaluationSerializer(serializers.ModelSerializer):
    criteria_scores = serializers.JSONField(required=False)
    student_name = serializers.CharField(source="log.intern.get_full_name", read_only=True)
    company = serializers.CharField(source="log.placement.company_name", read_only=True)
    week_number = serializers.IntegerField(source="log.week_number", read_only=True)
    status = serializers.CharField(source="log.status", read_only=True)
    log_submitted_at = serializers.DateTimeField(source="log.submitted_at", read_only=True)

    class Meta:
        model = Evaluation
        fields = [
            "id",
            "log",
            "student_name",
            "company",
            "week_number",
            "status",
            "objectives",
            "rating",
            "comments",
            "recommendation",
            "criteria_scores",
            "total_score",
            "log_submitted_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "student_name",
            "company",
            "week_number",
            "status",
            "total_score",
            "log_submitted_at",
            "created_at",
            "updated_at",
        ]

    def validate_rating(self, value):
        if value is None:
            return value
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5.")
        return value

    def validate_criteria_scores(self, scores):
        if scores in (None, ""):
            return {}
        if not isinstance(scores, dict):
            raise serializers.ValidationError("criteria_scores must be a JSON object.")

        errors = {}
        for criterion_id_str, score in scores.items():
            try:
                criterion_id = int(criterion_id_str)
                criterion = EvaluationCriteria.objects.get(id=criterion_id)
            except (ValueError, EvaluationCriteria.DoesNotExist):
                errors[str(criterion_id_str)] = "Criterion does not exist."
                continue

            if not isinstance(score, (int, float)):
                errors[str(criterion_id_str)] = "Score must be numeric."
                continue

            if score < 0 or score > float(criterion.max_score):
                errors[str(criterion_id_str)] = (
                    f"Score must be between 0 and {criterion.max_score}."
                )

        if errors:
            raise serializers.ValidationError(errors)
        return scores

    def validate(self, attrs):
        criteria_scores = attrs.get("criteria_scores")
        rating = attrs.get("rating", getattr(self.instance, "rating", None))

        if (criteria_scores in (None, {}, "")) and rating is None:
            raise serializers.ValidationError(
                "Provide either criteria_scores or a rating."
            )
        return attrs

    def _calculate_total_score(self, scores, rating):
        if scores:
            total = 0.0
            for criterion_id_str, score in scores.items():
                criterion = EvaluationCriteria.objects.get(id=int(criterion_id_str))
                weighted = (score / float(criterion.max_score)) * float(criterion.weight) * 100
                total += weighted
            return round(total, 2)

        if rating is not None:
            return round((float(rating) / 5.0) * 100, 2)

        return 0

    def create(self, validated_data):
        scores = validated_data.get("criteria_scores", {}) or {}
        rating = validated_data.get("rating")
        validated_data["total_score"] = self._calculate_total_score(scores, rating)
        validated_data["criteria_scores"] = scores
        return Evaluation.objects.create(**validated_data)

    def update(self, instance, validated_data):
        scores = validated_data.get("criteria_scores", instance.criteria_scores or {})
        rating = validated_data.get("rating", instance.rating)
        validated_data["criteria_scores"] = scores
        validated_data["total_score"] = self._calculate_total_score(scores, rating)
        return super().update(instance, validated_data)


class ReviewActionSerializer(serializers.ModelSerializer):
    action_by_name = serializers.CharField(source="action_by.get_full_name", read_only=True)
    action_by_role = serializers.CharField(source="action_by.role", read_only=True)

    class Meta:
        model = ReviewAction
        fields = [
            "action_by_name",
            "action_by_role",
            "action",
            "comment",
            "timestamp",
        ]


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            "id",
            "message",
            "notification_type",
            "is_read",
            "created_at",
        ]
        read_only_fields = fields
