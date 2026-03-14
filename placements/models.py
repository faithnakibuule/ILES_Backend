from django.db import models
<<<<<<< HEAD

# Create your models here.
=======
from users.models import CustomUser

# Create your models here.

class InternshipPlacement(models.Model):
    STATUS_CHOICES = [
        ('PENDING','Pending'),
        ('ACTIVE','Active'),
        ('COMPLETED','Completed'),
        ('CANCELLED','Cancelled')
    ]
    
    student = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name = 'placements',
        limit_choices_to={'role': 'student'}
    )
    workplace_supervisor = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name = 'supervised_placements',
        limit_choices_to={'role':'workplace_supervisor'}
    )
    company_name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING')
    
    def __str__(self):
        return f"{self.student.username} at {self.company_name} ({self.status})"
>>>>>>> 37ef7494ad109a3cf8f1ecfdf572aa9674e4feda
