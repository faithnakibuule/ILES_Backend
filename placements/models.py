from django.db import models
from users.models import CustomUser

# Create your models here.


class Company(models.Model):
    name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

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
    
    academic_supervisor = models.ForeignKey(
    CustomUser,
    on_delete=models.SET_NULL,
    related_name='academic_supervised_placements',
    limit_choices_to={'role': 'academic_supervisor'},
    null=True,
    blank=True
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="placements",
        null=True,
        blank=True,
    )
    company_name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING')

    def save(self, *args, **kwargs):
        if self.company_id:
            self.company_name = self.company.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.email} at {self.company_name} ({self.status})"
