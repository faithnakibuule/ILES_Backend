from django.db import models
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
                max_length=10,
                choices=STATUS_CHOICES,
                default='DRAFT'
    )
    submitted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [['intern', 'week_number']]
    
    def __str__(self):
        return f"Week {self.week_number} - {self.intern.username}"
