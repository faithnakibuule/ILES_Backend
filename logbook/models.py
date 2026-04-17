from django.utils import timezone
from django.db import models
from datetime import timedelta
from users.models import CustomUser
from placements.models import InternshipPlacement

class WeeklyLog(models.Model):
    STATUS_CHOICES =[
        ('DRAFT', 'Draft'),
        ('SUBMITTED', 'Submitted'),
        ('REVIEWED', 'Reviewed'),
        ('APPROVED', 'Approved'),
    ]

    intern = models.ForeignKey( CustomUser,
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
    activities =models.TextField()
    learning_points = models.TextField()
    status = models.CharField(
                max_length=20,
                choices=STATUS_CHOICES,
                default='DRAFT'
    )

    submitted_at = models.DateTimeField(null=True, blank=True)
    supervisor_comment = models.TextField(null=True, blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._old_status = self.status #remember status when object is loaded

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._old_status = self.status  #update memory after saving
     
    @property
    def is_overdue(self):
        if not self.submitted_at:
            #not submitted yet, check if deadline has passed
            deadline = self.placement.start_date + timedelta(days=7 * self.week_number)
            return timezone.now().date() > deadline
        #check if submitted after deadline
        deadline = self.placement.start_date + timedelta(days=7 * self.week_number)
        return self.submitted_at.date() > deadline
    class Meta:
        unique_together = [['intern', 'week_number']]
    
    def __str__(self):
        return f"Week {self.week_number} - {self.intern.email}"
class ReviewAction(models.Model):
    log = models.ForeignKey(
        WeeklyLog, 
        on_delete=models.CASCADE,
        related_name='logbook_review_actions'
    )
    supervisor = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='review_actions',
        limit_choices_to={'role': 'workplace_supervisor'}
    )
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering =['-created_at']

    def __str__(self):
        return f"Review by {self.supervisor.email} on Week {self.log.week_number}"


 
    