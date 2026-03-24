from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('workplace_supervisor', 'Workplace Supervisor'),
        ('academic_supervisor', 'Academic Supervisor'),
        ('admin', 'Admin'),
    ]

    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default='student'
    )

    def __str__(self):
        return f"{self.email} ({self.role})"


class InternshipPlacement(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='placements')
    workplace_supervisor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='supervised_placements')
    company_name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.student.email} at {self.company_name}"


class WeeklyLog(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('REVIEWED', 'Reviewed'),
        ('APPROVED', 'Approved'),
    ]

    intern = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='logs')
    placement = models.ForeignKey(InternshipPlacement, on_delete=models.CASCADE, related_name='logs')
    week_number = models.PositiveSmallIntegerField()
    activities = models.TextField()
    learning_points = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='DRAFT')
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('intern', 'week_number')
        ordering = ['intern', 'week_number']

    def __str__(self):
        return f"Week {self.week_number} - {self.intern.email}"


class ReviewAction(models.Model):
    ACTION_CHOICES = [
        ('SUBMITTED', 'Submitted'),
        ('REVIEWED', 'Reviewed'),
        ('SENT_BACK', 'Sent Back'),
        ('APPROVED', 'Approved'),
        ('SCORED', 'Scored'),
    ]

    log = models.ForeignKey(WeeklyLog, on_delete=models.CASCADE, related_name='review_actions')
    action_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='actions')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    comment = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.action} on {self.log} by {self.action_by.email}"


class Evaluation(models.Model):
    log = models.OneToOneField(WeeklyLog, on_delete=models.CASCADE, related_name='evaluation')
    academic_supervisor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='evaluations')
    total_score = models.DecimalField(max_digits=5, decimal_places=2, help_text="Weighted total score (0-100)")
    criteria_scores = models.JSONField(default=dict, help_text="JSON with criterion_id: score")
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Evaluation for {self.log}"