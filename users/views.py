from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomUserSerializer, RegisterSerializer,UserUpdateSerializer, CustomTokenObtainPairSerializer
from .models import CustomUser
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated 
from rest_framework.response import Response
from .serializers import MeSerializer
# Create your views here.

class RegisterView(generics.CreateAPIView):#This view allows users to register by creating a new CustomUser instance
    queryset = CustomUser.objects.all()    # using the RegisterSerializer. It is accessible to anyone (AllowAny permission).
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

class MeView(generics.RetrieveUpdateAPIView):#This view allows authenticated users to retrieve their own user information.
    serializer_class = CustomUserSerializer #
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return UserUpdateSerializer
        return CustomUserSerializer

    def get_object(self):
        return self.request.user
    
    
class CustomTokenObtainPairView(TokenObtainPairView):# It uses the CustomTokenObtainPairSerializer to customize the token generation process
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]

class WeeklyLogListView(generics.ListCreateAPIView):
    queryset = []
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return []
    
class MeView2(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = MeSerializer(request.user)
        return Response(serializer.data)
    
        

