from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    AdminUserSerializer,
    CourseSerializer,
    CustomTokenObtainPairSerializer,
    CustomUserSerializer,
    RegisterSerializer,
    UserUpdateSerializer,
)
from .models import Course, CustomUser
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .permissions import IsAdminUser
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated 
from rest_framework.response import Response
from .serializers import MeSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Count
import csv
from django.http import HttpResponse
from .throttles import LoginRateThrottle, RegisterRateThrottle
class RegisterView(generics.CreateAPIView):#This view allows users to register by creating a new CustomUser instance
    queryset = CustomUser.objects.all()    # using the RegisterSerializer. It is accessible to anyone (AllowAny permission).
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [RegisterRateThrottle]

class MeView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/auth/me/ — returns current user's profile (CustomUserSerializer)
    PATCH /api/auth/me/ — updates name/phone (UserUpdateSerializer), 
                          then returns the updated profile using CustomUserSerializer
                          so the frontend gets full_name back immediately.
    """
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return UserUpdateSerializer
        return CustomUserSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        # Run the PATCH using UserUpdateSerializer (validates + saves)
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = UserUpdateSerializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_user = serializer.save()

        # Return the full profile using CustomUserSerializer so frontend
        # gets full_name, email, role — not just the write-only fields
        response_serializer = CustomUserSerializer(updated_user)
        return Response(response_serializer.data)
    
    
class CustomTokenObtainPairView(TokenObtainPairView):# It uses the CustomTokenObtainPairSerializer to customize the token generation process
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginRateThrottle]


class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by("name")
    serializer_class = CourseSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAdminUser()]

class WeeklyLogListView(generics.ListCreateAPIView):
    queryset = []
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return []
    
class MeView2(APIView):
    permission_classes = [IsAuthenticated]

class AdminUserViewSet(viewsets.ModelViewSet):
    """
    Admin-only control panel for managing all users.
    Supports filtering by role, searching by name/email,
    creating users, and deactivating users.
    """
    queryset = CustomUser.objects.exclude(role='admin').order_by('date_joined')
    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAuthenticated,IsAdminUser]
    
    # What fields can be filtered with ?role=student
    filterset_fields = ['role','is_active', 'company']
    
    # What fields does ?search= look through
    search_fields = ['first_name','last_name','email']
    
    # What fields can be sorted with ?ordering=email
    ordering_fields = ['date_joined', 'first_name', 'last_name', 'email']

    def get_queryset(self):
        queryset = super().get_queryset().select_related("company")
        company_id = self.request.query_params.get("company_id")
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        return queryset
    
    @action(detail=True, methods=['patch']) 
    def deactivate(self,request,pk=None):
        """
        Custom action: PATCH /api/admin/users/{id}/deactivate/
        Sets is_active=False without deleting the user.
        """
        user = self.get_object()
        user.is_active = False
        user.save()
        
        return Response(
            {'message': f'{user.email} has been deactivated.'},
            status=status.HTTP_200_OK
        )
     
    
    
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


class ExportPlacementsView(APIView):
    """
    GET /api/admin/export/placements/
    Downloads a CSV file of all placements.
    Admin only.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        # 1. Create an HttpResponse that tells browser to download a CSV
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="placements.csv"'

        # 2. Create a CSV writer that writes directly into the response
        writer = csv.writer(response)

        # 3. Write the header row — these become the column names in Excel
        writer.writerow([
            'ID',
            'Student',
            'Student Email',
            'Company',
            'Workplace Supervisor',
            'Academic Supervisor',
            'Start Date',
            'End Date',
            'Status',
        ])

        # 4. Fetch all placements with related user data in one query
        from placements.models import InternshipPlacement
        placements = InternshipPlacement.objects.select_related(
            'student',
            'workplace_supervisor',
            'academic_supervisor'
        ).all()

        # 5. Write one row per placement
        for placement in placements:
            writer.writerow([
                placement.id,
                f"{placement.student.first_name} {placement.student.last_name}".strip(),
                placement.student.email,
                placement.company_name,
                f"{placement.workplace_supervisor.first_name} {placement.workplace_supervisor.last_name}".strip(),
                # Academic supervisor is optional — may be None
                f"{placement.academic_supervisor.first_name} {placement.academic_supervisor.last_name}".strip()
                if placement.academic_supervisor else "Not Assigned",
                placement.start_date,
                placement.end_date,
                placement.status,
            ])

        return response  # Django sends this as a file download


class ExportLogsView(APIView):
    """
    GET /api/admin/export/logs/
    Downloads a CSV file of all logs with status and scores.
    Admin only.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        # 1. Create the CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="logs.csv"'

        writer = csv.writer(response)

        # 2. Header row
        writer.writerow([
            'ID',
            'Student',
            'Student Email',
            'Week Number',
            'Status',
            'Submitted At',
            'Total Score',
        ])

        # 3. Fetch all logs — prefetch evaluations for score data
        from logbook.models import WeeklyLog
        logs = WeeklyLog.objects.select_related(
            'intern'
        ).prefetch_related(
            'evaluations'  # fetch all evaluations in one query
        ).all()

        # 4. Write one row per log
        for log in logs:
            # Get the latest evaluation score if it exists
            latest_evaluation = log.evaluations.first()
            score = latest_evaluation.total_score if latest_evaluation else "Not Scored"

            writer.writerow([
                log.id,
                f"{log.intern.first_name} {log.intern.last_name}".strip(),
                log.intern.email,
                log.week_number,
                log.status,
                log.submitted_at,
                score,
            ])

        return response
