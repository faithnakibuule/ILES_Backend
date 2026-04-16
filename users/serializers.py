from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from .models import CustomUser
from reviews.models import Notification
User = get_user_model

#shows user data
class CustomUserSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()
    
    def get_fullname(self,obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    
    class Meta:
        model = CustomUser
        fields = ['id','email','role','fullname', 'phone']
 
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
        return data
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        return CustomUser.objects.create_user(
            email = validated_data['email'],
            password = validated_data['password'],
            role = validated_data.get('role','student')
        )            

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:

        model = CustomUser
        fields = ['first_name','last_name','phone']

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
