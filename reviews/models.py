# reviews/models.py

from django.db import models
from django.conf import settings        # Safe reference to AUTH_USER_MODEL
from logbook.models import WeeklyLog    # WeeklyLog is still needed for Evaluation & ReviewAction


class EvaluationCriteria(models.Model):
    """Defines the marking rubric — each criterion has a name, description and max score."""
    name        = models.CharField(max_length=255)
    description = models.TextField()
    max_score   = models.PositiveIntegerField()
    weight      = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.name} (max: {self.max_score})"


class Evaluation(models.Model):
    """Records a score given by an academic supervisor for a specific weekly log."""
    log = models.ForeignKey(
        WeeklyLog,
        on_delete=models.CASCADE,
        related_name='evaluations'          # log.evaluations.all()
    )
    academic_supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,           # Fixed — points to CustomUser safely
        on_delete=models.CASCADE,
        related_name='evaluations',
        limit_choices_to={'role': 'academic_supervisor'}  # Only academic supervisors can evaluate
    )
    total_score     = models.DecimalField(max_digits=6, decimal_places=2)
    criteria_scores = models.JSONField()        # Stores per-criterion breakdown as JSON
    comments        = models.TextField()
    created_at      = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evaluation for {self.log} by {self.academic_supervisor.username}"


class ReviewAction(models.Model):
    """
    Audit trail — every approve, send-back, or score event is recorded here.
    One WeeklyLog can have MANY ReviewActions over its lifetime.
    """
    ACTION_CHOICES = [
        ('APPROVED',  'Approved'),
        ('SENT_BACK', 'Sent Back'),
        ('SCORED',    'Scored'),
    ]

    log = models.ForeignKey(
        WeeklyLog,
        on_delete=models.CASCADE,
        related_name='review_actions'       # log.review_actions.all()
    )
    action_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,           # Any user role can perform an action
        on_delete=models.CASCADE,
        related_name='actions_taken'        # user.actions_taken.all()
    )
    action    = models.CharField(max_length=20, choices=ACTION_CHOICES)
    comment   = models.TextField(blank=True, default='')
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']           # Most recent action appears first

    def __str__(self):
        return f"{self.action_by} → {self.action} on Log #{self.log.id}"


class Notification(models.Model):
    """
    The notification inbox — every system event creates one row here
    for the relevant recipient to read.
    """

    class NotificationType(models.TextChoices):
        # Left side = stored in DB | Right side = shown in UI
        LOG_SUBMITTED  = 'LOG_SUBMITTED',  'Log Submitted'
        LOG_REVIEWED   = 'LOG_REVIEWED',   'Log Reviewed'
        LOG_SENT_BACK  = 'LOG_SENT_BACK',  'Log Sent Back'
        LOG_APPROVED   = 'LOG_APPROVED',   'Log Approved'
        SCORE_ASSIGNED = 'SCORE_ASSIGNED', 'Score Assigned'

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,           # Any user can receive a notification
        on_delete=models.CASCADE,
        related_name='notifications'        # user.notifications.all()
    )
    message           = models.TextField()                          # The human-readable message
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices    # Enforces fixed list — no typos allowed
    )
    is_read    = models.BooleanField(default=False)                 # Unread by default
    created_at = models.DateTimeField(auto_now_add=True)           # Set once on creation

    class Meta:
        ordering = ['-created_at']          # Newest notification appears first

    def __str__(self):
        return f"[{self.notification_type}] → {self.recipient.username}"