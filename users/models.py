from django.db import models
from django.contrib.auth.models import AbstractUser,BaseUserManager
# Create your models here.
#This custom user model allows us to use email as the unique identifier instead of username, and also includes a role field to differentiate between different types of users in the system. The CustomUserManager handles the creation of regular users and superusers, ensuring that the necessary fields are set correctly.
#the builder-knows how to create a user correctly
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        
        email = self.normalize_email(email)#lowercase the email for consistency
        user = self.model(email=email, **extra_fields)
        user.set_password(password)#This hashes the password
        user.save(using=self._db)
        return user
    #superusers need full system access, so we set is_staff and is_superuser to True
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser',True)
        return self.create_user(email, password, **extra_fields)   
    
#defines what auser record holds in the database    
class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('student','Student'),
        ('workplace_supervisor','Workplace Supervisor'),
        ('academic_supervisor','Academic Supervisor'),
        ('admin','Admin'),
    ]
    
    username = None #we won't use the default username field
    email = models.EmailField(unique = True)#replace it with email
    role = models.CharField(
        max_length = 30,
        choices = ROLE_CHOICES,
        default = 'student'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [] #email is required by default, so we don't need to add it here
    phone = models.CharField(max_length=20, blank=True, null=True) #optional phone number field
    
    objects = CustomUserManager()#tells Django to use our custom manager for user creation and management
    def __str__(self):
        return f"{self.email} ({self.role})"

