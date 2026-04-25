from django.db import models

from logbook.models import WeeklyLog
from django.contrib.auth import get_user_model

User = get_user_model()


class Evaluation(models.Model):
    log = models.ForeignKey(WeeklyLog, on_delete=models.CASCADE)
    academic_supervisor = models.ForeignKey(User, on_delete=models.CASCADE)

    criteria_scores = models.JSONField(default=dict)
    total_score = models.FloatField()
    comments = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

# Create your models here.
