

from rest_framework import serializers
from .models import Evaluation, EvaluationCriteria


class EvaluationSerializer(serializers.ModelSerializer):
    criteria_scores = serializers.JSONField(write_only=True)

    class Meta:
        model = Evaluation
        fields = ['id', 'log', 'academic_supervisor', 'comments', 'criteria_scores', 'total_score', 'created_at']
        read_only_fields = ['total_score', 'created_at']

    def validate_criteria_scores(self, scores):
        if not isinstance(scores, dict):
            raise serializers.ValidationError("criteria_scores must be a JSON object.")

        errors = {}

        for criterion_id_str, score in scores.items():
            try:
                criterion_id = int(criterion_id_str)
                criterion = EvaluationCriteria.objects.get(id=criterion_id)
            except (ValueError, EvaluationCriteria.DoesNotExist):
                errors[criterion_id_str] = f"Criterion '{criterion_id_str}' does not exist."
                continue

            if not isinstance(score, (int, float)):
                errors[criterion_id_str] = "Score must be a number."
                continue

            if score < 0 or score > float(criterion.max_score):
                errors[criterion_id_str] = (
                    f"Score {score} is invalid. "
                    f"Must be between 0 and {criterion.max_score}."
                )

        if errors:
            raise serializers.ValidationError(errors)

        return scores

    def create(self, validated_data):
        scores = validated_data.pop('criteria_scores')

        total = 0.0
        for criterion_id_str, score in scores.items():
            criterion = EvaluationCriteria.objects.get(id=int(criterion_id_str))
            weighted = (score / float(criterion.max_score)) * float(criterion.weight) * 100
            total += weighted

        validated_data['total_score'] = round(total, 2)
        validated_data['criteria_scores'] = scores

        evaluation = Evaluation.objects.create(**validated_data)
        return evaluation