from .default_criteria import DEFAULT_EVALUATION_CRITERIA
from .models import EvaluationCriteria


def ensure_default_evaluation_criteria():
    for item in DEFAULT_EVALUATION_CRITERIA:
        EvaluationCriteria.objects.update_or_create(
            name=item["name"],
            defaults={
                "description": item["description"],
                "max_score": item["max_score"],
                "weight": item["weight"],
            },
        )
