from django.conf import settings
from django.db import models

from logbook.models import WeeklyLog


class EvaluationCriteria(models.Model):
    """Defines the marking rubric for academic evaluations."""

    name = models.CharField(max_length=255)
    description = models.TextField()
    max_score = models.PositiveIntegerField()
    weight = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.name} (max: {self.max_score})"


class Evaluation(models.Model):
    """Academic evaluation recorded against a reviewed weekly log."""

    log = models.ForeignKey(
        WeeklyLog,
        on_delete=models.CASCADE,
        related_name="evaluations",
    )
    academic_supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="evaluations",
        limit_choices_to={"role": "academic_supervisor"},
    )
    objectives = models.TextField(blank=True, default="")
    rating = models.PositiveSmallIntegerField(null=True, blank=True)
    total_score = models.DecimalField(max_digits=6, decimal_places=2)
    criteria_scores = models.JSONField(default=dict, blank=True)
    comments = models.TextField(blank=True, default="")
    recommendation = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Evaluation for {self.log} by {self.academic_supervisor.email}"


class ReviewAction(models.Model):
    ACTION_CHOICES = [
        ("APPROVED", "Approved"),
        ("SENT_BACK", "Sent Back"),
        ("SCORED", "Scored"),
    ]

    log = models.ForeignKey(
        "logbook.WeeklyLog",
        on_delete=models.CASCADE,
        related_name="review_actions",
    )
    action_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="actions_taken",
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    comment = models.TextField(blank=True, default="")
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.action_by} -> {self.action} on Log #{self.log.id}"


class Notification(models.Model):
    class NotificationType(models.TextChoices):
        LOG_SUBMITTED = "LOG_SUBMITTED", "Log Submitted"
        LOG_REVIEWED = "LOG_REVIEWED", "Log Reviewed"
        LOG_SENT_BACK = "LOG_SENT_BACK", "Log Sent Back"
        LOG_APPROVED = "LOG_APPROVED", "Log Approved"
        SCORE_ASSIGNED = "SCORE_ASSIGNED", "Score Assigned"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.notification_type}] -> {self.recipient.email}"
