from django.db import models
from django.utils import timezone
from django.utils.dateparse import parse_date
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

    def _coerce_date(self, value):
        if isinstance(value, str):
            return parse_date(value)
        return value

    def calculate_status(self, today=None):
        if self.status == "CANCELLED":
            return "CANCELLED"

        today = today or timezone.localdate()
        start_date = self._coerce_date(self.start_date)
        end_date = self._coerce_date(self.end_date)

        if end_date and end_date < today:
            return "COMPLETED"
        if start_date and end_date and start_date <= today <= end_date:
            return "ACTIVE"
        return "PENDING"

    def save(self, *args, **kwargs):
        if self.company_id:
            self.company_name = self.company.name

        update_fields = kwargs.get("update_fields")
        status_explicitly_saved = update_fields and "status" in update_fields
        if (
            not status_explicitly_saved
            and self.start_date
            and self.end_date
            and self.status != "CANCELLED"
        ):
            self.status = self.calculate_status()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.email} at {self.company_name} ({self.status})"
