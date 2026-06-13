from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, permissions, viewsets, filters, status
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import (
    AdminUserSerializer,
    CollegeSerializer,
    CourseSerializer,
    CustomTokenObtainPairSerializer,
    CustomUserSerializer,
    RegisterSerializer,
    UserUpdateSerializer,
    MeSerializer,
)
from .models import College, Course, CustomUser
from django_filters.rest_framework import DjangoFilterBackend
from .permissions import IsAdminUser
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q
from django.db.models import ProtectedError
import csv
from urllib.parse import urlencode
from django.http import HttpResponse
from .throttles import LoginRateThrottle, RegisterRateThrottle
from .email_utils import send_password_reset_email

User = get_user_model()
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
    queryset = Course.objects.select_related("college").all().order_by("name")
    serializer_class = CourseSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAdminUser()]

    def get_queryset(self):
        queryset = Course.objects.select_related("college").order_by("name")
        college_id = self.request.query_params.get("college_id")
        if college_id:
            queryset = queryset.filter(college_id=college_id)
        return queryset

    def destroy(self, request, *args, **kwargs):
        course = self.get_object()
        if course.students.exists():
            return Response(
                {"message": "This course cannot be deleted because students are still assigned to it."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return super().destroy(request, *args, **kwargs)


class CollegeViewSet(viewsets.ModelViewSet):
    serializer_class = CollegeSerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsAdminUser()]

    def get_queryset(self):
        return College.objects.annotate(
            academic_supervisor_count=Count(
                "academic_supervisors",
                filter=Q(academic_supervisors__role="academic_supervisor"),
            ),
            course_count=Count("courses", distinct=True),
        ).order_by("name")

    def destroy(self, request, *args, **kwargs):
        college = self.get_object()
        has_academics = college.academic_supervisors.filter(role="academic_supervisor").exists()
        has_courses = college.courses.exists()
        if has_academics or has_courses:
            message = "This college cannot be deleted because it still has "
            reasons = []
            if has_academics:
                reasons.append("academic supervisors assigned to it")
            if has_courses:
                reasons.append("courses linked to it")
            return Response(
                {"message": f"{message}{' and '.join(reasons)}."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            return super().destroy(request, *args, **kwargs)
        except ProtectedError:
            return Response(
                {"message": "This college cannot be deleted because related records still depend on it."},
                status=status.HTTP_400_BAD_REQUEST,
            )

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
        queryset = super().get_queryset().select_related("company", "course__college", "college")
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

class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = (request.data.get("email") or "").strip().lower()
        frontend_base_url = settings.FRONTEND_URL.rstrip("/")
        reset_path = getattr(settings, "FRONTEND_PASSWORD_RESET_PATH", "/reset-password")
        if not reset_path.startswith("/"):
            reset_path = f"/{reset_path}"

        delivery = "skipped"
        if email and frontend_base_url:
            user = User.objects.filter(email__iexact=email, is_active=True).first()
            
            if user:
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                reset_url = f"{frontend_base_url}{reset_path}?{urlencode({'uid': uid, 'token': token})}"
                # Send email — gracefully handles Render's SMTP block
                # Returns False if email fails but never crashes the request
                sent = send_password_reset_email(user, reset_url)
                delivery = (
                    "console"
                    if settings.EMAIL_BACKEND.endswith("console.EmailBackend")
                    else "smtp"
                )

        # Always return 200 — prevents user enumeration attacks
        # and prevents 500 crashes when Render blocks SMTP on free tier
        response_data = {
            "message": "Password reset email sent if account exists. Check inbox or spam folder to reset."
        }
        if settings.DEBUG:
            response_data["delivery"] = delivery
        return Response(response_data, status=status.HTTP_200_OK)

class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        uid = request.data.get("uid")
        token = request.data.get("token")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("new_password_confirm")

        if not all([uid, token, new_password, confirm_password]):
            return Response(
                {"message": "uid, token, new_password and new_password_confirm are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_password != confirm_password:
            return Response(
                {"message": "Passwords do not match."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id, is_active=True)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"message": "Invalid reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"message": "This reset link is invalid or has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            validate_password(new_password, user=user)
        except DjangoValidationError as exc:
            return Response(
                {"message": exc.messages[0]},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(new_password)
        user.save(update_fields=["password"])
        return Response({"message": "Password has been reset."}, status=status.HTTP_200_OK)
