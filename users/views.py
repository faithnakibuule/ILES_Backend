from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomUserSerializer, RegisterSerializer
from .models import CustomUser
# Create your views here.

class RegisterView(generics.CreateAPIView):#This view allows users to register by creating a new CustomUser instance
    queryset = CustomUser.objects.all()    # using the RegisterSerializer. It is accessible to anyone (AllowAny permission).
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

class MeView(generics.RetrieveAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user