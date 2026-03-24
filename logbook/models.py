from django.utils import timezone
from django.db import models
from datetime import timedelta
from users.models import CustomUser
from placements.models import InternshipPlacement

class WeeklyLog(models.Model):
    supervisor_comment = models.TextField(null=True, blank=True)

    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('REVIEWED', 'Reviewed'),
        ('APPROVED', 'Approved'),
    ]

    intern = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='weekly_logs',
        limit_choices_to={'role': 'student'}
    )
    placement = models.ForeignKey(
        InternshipPlacement,
        on_delete=models.CASCADE,
        related_name='weekly_logs'
    )
    week_number = models.PositiveIntegerField()
    activities = models.TextField()
    learning_points = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='DRAFT'
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_overdue(self):
        if not self.submitted_at:
            deadline = self.placement.start_date + timedelta(days=7 * self.week_number)
            return timezone.now().date() > deadline
        deadline = self.placement.start_date + timedelta(days=7 * self.week_number)
        return self.submitted_at.date() > deadline

    class Meta:
        unique_together = [['intern', 'week_number']]

    def __str__(self):
        return f"Week {self.week_number} - {self.intern.email}"