from django.db import models
from django.utils import timezone
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

    def calculate_status(self, today=None):
        if self.status == "CANCELLED":
            return "CANCELLED"

        today = today or timezone.localdate()
        if self.end_date and self.end_date < today:
            return "COMPLETED"
        if self.start_date and self.start_date <= today <= self.end_date:
            return "ACTIVE"
        return "PENDING"

    def save(self, *args, **kwargs):
        if self.company_id:
            self.company_name = self.company.name
        if self.start_date and self.end_date and self.status != "CANCELLED":
            self.status = self.calculate_status()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.email} at {self.company_name} ({self.status})"
