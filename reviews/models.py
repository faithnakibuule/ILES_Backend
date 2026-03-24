# reviews/models.py
from django.db import models
from django.conf import settings
from users.models import CustomUser
from logbook.models import WeeklyLog

class EvaluationCriteria(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    max_score = models.PositiveIntegerField()
    weight = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.name} (max: {self.max_score})"

class Evaluation(models.Model):
    log = models.ForeignKey(
        WeeklyLog,
        on_delete=models.CASCADE,
        related_name='evaluations'
    )
    academic_supervisor = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='evaluations',
        limit_choices_to={'role': 'academic_supervisor'}
    )
    total_score = models.DecimalField(max_digits=6, decimal_places=2)
    criteria_scores = models.JSONField()
    comments = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evaluation for {self.log} by {self.academic_supervisor.email}"

class ReviewAction(models.Model):
    """
    Audit trail: every approve, send-back, or score event is recorded here.
    One WeeklyLog can have MANY ReviewActions over its lifetime.
    """
    ACTION_CHOICES = [
        ('APPROVED', 'Approved'),
        ('SENT_BACK', 'Sent Back'),
        ('SCORED', 'Scored'),
    ]

    log = models.ForeignKey(
        WeeklyLog,
        on_delete=models.CASCADE,
        related_name='review_actions'
    )
    action_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='actions_taken'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    comment = models.TextField(blank=True, default='')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.action_by.email} → {self.action} on Log #{self.log.id}"