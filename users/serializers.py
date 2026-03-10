from rest_framework import serializers
from .models import CustomUser

#shows user data
class CustomUserSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()
    
    def get_fullname(self,obj):
        return f"{obj.first_name} {obj.last_name}".strip()
    
    class Meta:
        model = CustomUser
        fields = ['id','email','role','fullname']
 
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
        user = CustomUser.objects.create_user(
            email = validated_data['email'],
            password = validated_data['password'],
            role = validated_data.get('role','student')
        )            
        return user
    
class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model=CustomUser
        fields = ['first_name','last_name','phone']    