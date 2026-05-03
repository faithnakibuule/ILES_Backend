from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from .models import CustomUser, Course
from reviews.models import Notification
from placements.models import Company

User = get_user_model()

#shows user data
class CustomUserSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    course = serializers.SerializerMethodField()
    
    def get_fullname(self,obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_full_name(self, obj):
        return self.get_fullname(obj)

    def get_company(self, obj):
        if not obj.company_id:
            return None
        return {
            "id": obj.company_id,
            "name": obj.company.name,
        }

    def get_course(self, obj):
        if not getattr(obj, 'course_id', None):
            return None
        return {
            "id": obj.course_id,
            "name": obj.course.name,
        }
    
    class Meta:
        model = CustomUser
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'role',
            'fullname',
            'full_name',
            'phone',
            'company',
            'course',
            'is_active',
        ]
 
 #validates and creates a new user       
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        source='company',
        write_only=True,
        required=False,
        allow_null=True,
    )
    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        source='course',
        write_only=True,
        required=False,
        allow_null=True,
    )
    course_name = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    
    class Meta:
        model = CustomUser
        fields = [
            'email',
            'role',
            'first_name',
            'last_name',
            'password',
            'confirm_password',
            'company_id',
            'course_id',
            'course_name',
        ]
        
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        
        # Check email uniqueness
        if CustomUser.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Email already exists")
        
        # Block admin role registration
        if data.get('role') == 'admin':
            raise serializers.ValidationError("Admin accounts cannot be created via registration.")

        role = data.get('role', 'student')
        company = data.get('company')
        course = data.get('course')
        course_name = (data.get('course_name') or '').strip()

        if role == 'student' and not course and course_name:
            course, _ = Course.objects.get_or_create(name=course_name)
            data['course'] = course

        # Workplace supervisors must have a company assigned
        if role == 'workplace_supervisor' and not company:
            raise serializers.ValidationError(
                {"company_id": "Workplace supervisors must select a company during registration."}
            )

        # Only workplace supervisors can have company
        if role != 'workplace_supervisor' and company:
            raise serializers.ValidationError(
                {"company_id": "Only workplace supervisors can select a company."}
            )

        # Only students can have course
        if role != 'student' and course:
            raise serializers.ValidationError(
                {"course_id": "Only students can select a course."}
            )

        return data
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        validated_data.pop('course_name', None)
        return CustomUser.objects.create_user(
            email = validated_data['email'],
            password = validated_data['password'],
            role = validated_data.get('role','student'),
            first_name = validated_data.get('first_name', ''),
            last_name = validated_data.get('last_name', ''),
            company = validated_data.get('company'),
            course = validated_data.get('course'),
        )            

class UserUpdateSerializer(serializers.ModelSerializer):
    """
    PATCH /api/auth/me/
    
    Accepts full_name (a single display string) from the frontend,
    splits it into first_name + last_name, and saves both.
    Also accepts phone. 
    """
    full_name = serializers.CharField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = CustomUser
        fields = ['full_name', 'first_name', 'last_name', 'phone']

    def update(self, instance, validated_data):
        # Pop full_name — it's not a real model field, we need to split it
        full_name = validated_data.pop('full_name', None)

        if full_name is not None:
            parts = full_name.strip().split(' ', 1)      # split on FIRST space only
            instance.first_name = parts[0]               # everything before first space
            instance.last_name  = parts[1] if len(parts) > 1 else ''  # rest, or blank

        if 'first_name' in validated_data:
            instance.first_name = validated_data['first_name']

        if 'last_name' in validated_data:
            instance.last_name = validated_data['last_name']

        # phone IS a real model field — standard update
        if 'phone' in validated_data:
            instance.phone = validated_data['phone']

        instance.save()
        return instance


class AdminUserSerializer(serializers.ModelSerializer):
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        source="company",
        write_only=True,
        required=False,
        allow_null=True,
    )
    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        source="course",
        write_only=True,
        required=False,
        allow_null=True,
    )
    company = serializers.SerializerMethodField()
    course = serializers.SerializerMethodField()
    fullname = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "fullname",
            "role",
            "phone",
            "is_active",
            "company",
            "company_id",
            "course",
            "course_id",
            "password",
            "date_joined",
        ]
        read_only_fields = ["id", "fullname", "company", "course", "date_joined"]

    def get_fullname(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_company(self, obj):
        if not obj.company_id:
            return None
        return {
            "id": obj.company_id,
            "name": obj.company.name,
        }

    def get_course(self, obj):
        if not getattr(obj, 'course_id', None):
            return None
        return {
            "id": obj.course_id,
            "name": obj.course.name,
        }

    def validate(self, attrs):
        role = attrs.get("role", getattr(self.instance, "role", None))
        company = attrs.get("company", getattr(self.instance, "company", None))
        course = attrs.get("course", getattr(self.instance, "course", None))

        if role == "workplace_supervisor" and not company:
            raise serializers.ValidationError(
                {"company_id": "Workplace supervisors must be assigned to a company."}
            )

        if role != "workplace_supervisor" and "company" in attrs:
            attrs["company"] = None

        if role != "student" and "course" in attrs:
            attrs["course"] = None

        if not self.instance and not attrs.get("password"):
            raise serializers.ValidationError({"password": "Password is required."})

        return attrs

        if role == "workplace_supervisor" and not company:
            raise serializers.ValidationError(
                {"company_id": "Workplace supervisors must be assigned to a company."}
            )

        if role != "workplace_supervisor" and "company" in attrs:
            attrs["company"] = None

        if not self.instance and not attrs.get("password"):
            raise serializers.ValidationError({"password": "Password is required."})

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        return CustomUser.objects.create_user(password=password, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save(update_fields=["password"])
        return user

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['role'] = user.role
        token['full_name'] = f"{user.first_name} {user.last_name}".strip()
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user_data = CustomUserSerializer(self.user).data
        data["user"] = user_data
        data["role"] = self.user.role
        data["email"] = self.user.email
        data["full_name"] = user_data.get("full_name", "")
        return data

class MeSerializer(serializers.ModelSerializer):
    unread_notifications = serializers.SerializerMethodField()
    fullname = serializers.SerializerMethodField()

    def get_unread_notifications(self, user):
        return Notification.objects.filter(
            recipient = user,
            is_read = False
        ).count()
    
    def get_fullname(self,obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    class Meta:
        model = User
        fields = ['id', 'email','fullname', 'role','unread_notifications']
        read_only_fields = fields


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id', 'name']
        read_only_fields = ['id']
