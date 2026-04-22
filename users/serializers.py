from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from .models import CustomUser
from reviews.models import Notification
from placements.models import Company

User = get_user_model()

#shows user data
class CustomUserSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    
    def get_fullname(self,obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_company(self, obj):
        if not obj.company_id:
            return None
        return {
            "id": obj.company_id,
            "name": obj.company.name,
        }
    
    class Meta:
        model = CustomUser
        fields = ['id','email','role','fullname', 'phone', 'company', 'is_active']
 
 #validates and creates a new user       
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['email','role','password','confirm_password']
        
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        
        # Check email uniqueness
        if CustomUser.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError("Email already exists")

        return data
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        return CustomUser.objects.create_user(
            email = validated_data['email'],
            password = validated_data['password'],
            role = validated_data.get('role','student')
        )            

class UserUpdateSerializer(serializers.ModelSerializer):
    """
    PATCH /api/auth/me/
    
    Accepts full_name (a single display string) from the frontend,
    splits it into first_name + last_name, and saves both.
    Also accepts phone. 
    """
    full_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = CustomUser
        fields = ['full_name', 'phone']

    def update(self, instance, validated_data):
        # Pop full_name — it's not a real model field, we need to split it
        full_name = validated_data.pop('full_name', None)

        if full_name is not None:
            parts = full_name.strip().split(' ', 1)      # split on FIRST space only
            instance.first_name = parts[0]               # everything before first space
            instance.last_name  = parts[1] if len(parts) > 1 else ''  # rest, or blank

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
    company = serializers.SerializerMethodField()
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
            "password",
            "date_joined",
        ]
        read_only_fields = ["id", "fullname", "company", "date_joined"]

    def get_fullname(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_company(self, obj):
        if not obj.company_id:
            return None
        return {
            "id": obj.company_id,
            "name": obj.company.name,
        }

    def validate(self, attrs):
        role = attrs.get("role", getattr(self.instance, "role", None))
        company = attrs.get("company", getattr(self.instance, "company", None))

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
