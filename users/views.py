from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomUserSerializer, RegisterSerializer,UserUpdateSerializer, CustomTokenObtainPairSerializer
from .models import CustomUser
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated 
from rest_framework.response import Response
from .serializers import MeSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Count

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
    
        
# ── UserStatsView ─────────────────────────────────────────────────────────────
class UserStatsView(APIView):
    """
    GET /api/admin/stats/
    Returns programme-wide counts for the Admin Dashboard.
    Only accessible by authenticated users (admin role enforced on frontend).
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from users.models import CustomUser

        # Count users by role
        total_students = CustomUser.objects.filter(
            role='student'
        ).count()

        total_workplace_supervisors = CustomUser.objects.filter(
            role='workplace_supervisor'
        ).count()

        total_academic_supervisors = CustomUser.objects.filter(
            role='academic_supervisor'
        ).count()

        # Count placements — import here to avoid circular imports
        try:
            from placements.models import InternshipPlacement
            active_placements = InternshipPlacement.objects.filter(
                status='ACTIVE'
            ).count()
        except Exception:
            active_placements = 0

        # Count logs — import here to avoid circular imports
        try:
            from logbook.models import WeeklyLog
            total_logs = WeeklyLog.objects.count()
            approved_logs = WeeklyLog.objects.filter(
                status='APPROVED'
            ).count()
        except Exception:
            total_logs = 0
            approved_logs = 0

        return Response({
            'total_students': total_students,
            'total_workplace_supervisors': total_workplace_supervisors,
            'total_academic_supervisors': total_academic_supervisors,
            'active_placements': active_placements,
            'total_logs': total_logs,
            'approved_logs': approved_logs,
        }, status=status.HTTP_200_OK)
