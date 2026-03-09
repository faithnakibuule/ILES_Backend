from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('student','Student'),
        ('workplace_supervisor','Workplace Supervisor'),
        ('academic_supervisor','Academic Supervisor'),
        ('admin','Admin'),
    ]
    
    role = models.CharField(
        max_length = 30,
        choices = ROLE_CHOICES,
        default = 'student'
    )
    
    def __str__(self):
        return f"{self.username} ({self.role})"

