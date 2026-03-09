from rest_framework import serializers
from django.contrib.auth.models import User
User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [id, email, role, full_name]
        read_only_fields = [id]
        