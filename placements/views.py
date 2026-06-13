from django.db.models import Count, Q
from django.utils import timezone

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response

from logbook.models import WeeklyLog
from users.models import College, Course, CustomUser
from users.serializers import CollegeSerializer, CourseSerializer, CustomUserSerializer

from .models import Company, InternshipPlacement
from .serializers import CompanySerializer, PlacementSerializer


class PlacementViewSet(viewsets.ModelViewSet):
    serializer_class = PlacementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["status", "company_name", "company"]
    search_fields = [
        "student__first_name",
        "student__last_name",
        "student__email",
        "company_name",
    ]
    ordering_fields = ["start_date", "end_date", "status", "company_name"]

    def _sync_statuses(self):
        today = timezone.localdate()
        base = InternshipPlacement.objects.exclude(status="CANCELLED")
        base.filter(end_date__lt=today).exclude(status="COMPLETED").update(status="COMPLETED")
        base.filter(start_date__gt=today).exclude(status="PENDING").update(status="PENDING")
        base.filter(
            start_date__lte=today,
            end_date__gte=today,
        ).exclude(status="ACTIVE").update(status="ACTIVE")

    def get_queryset(self):
        user = self.request.user
        base = (
            InternshipPlacement.objects.select_related(
                "student",
                "workplace_supervisor",
                "academic_supervisor",
                "company",
            )
            .prefetch_related("weekly_logs")
            .order_by("-start_date", "-id")
        )

        if user.role == "admin":
            company_id = self.request.query_params.get("company_id")
            if company_id:
                base = base.filter(company_id=company_id)
            return base
        if user.role == "student":
            return base.filter(student=user)
        if user.role == "workplace_supervisor":
            return base.filter(workplace_supervisor=user)
        if user.role == "academic_supervisor":
            return base.filter(academic_supervisor=user)
        return InternshipPlacement.objects.none()

    def perform_create(self, serializer):
        if self.request.user.role != "admin":
            raise PermissionDenied("Only admins can create placements.")
        serializer.save()

    def perform_update(self, serializer):
        if self.request.user.role != "admin":
            raise PermissionDenied("Only admins can update placements.")
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        raise PermissionDenied("Placements should be cancelled instead of deleted.")

    def create(self, request, *args, **kwargs):
        if request.user.role != "admin":
            raise PermissionDenied("Only admins can create placements.")
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        if request.user.role != "admin":
            raise PermissionDenied("Only admins can update placements.")
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        if request.user.role != "admin":
            raise PermissionDenied("Only admins can update placements.")
        return super().partial_update(request, *args, **kwargs)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def companies(self, request):
        queryset = Company.objects.annotate(
            supervisor_count=Count(
                "users", filter=Q(users__role="workplace_supervisor")
            )
        ).order_by("name")
        serializer = CompanySerializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def placement_options(self, request):
        if request.user.role != "admin":
            raise PermissionDenied("Only admins can access placement options.")

        college_id = request.query_params.get("college_id")
        course_id = request.query_params.get("course_id")
        company_id = request.query_params.get("company_id")
        students = CustomUser.objects.filter(role="student", is_active=True).select_related(
            "course__college"
        ).order_by(
            "first_name", "last_name", "email"
        )
        academics = CustomUser.objects.filter(
            role="academic_supervisor", is_active=True
        ).select_related(
            "college"
        ).order_by("first_name", "last_name", "email")
        supervisors = CustomUser.objects.filter(
            role="workplace_supervisor", is_active=True
        ).select_related("company")
        courses = Course.objects.select_related("college").order_by("name")
        colleges = College.objects.annotate(
            academic_supervisor_count=Count(
                "academic_supervisors",
                filter=Q(academic_supervisors__role="academic_supervisor"),
            ),
            course_count=Count("courses", distinct=True),
        ).order_by("name")

        if college_id:
            academics = academics.filter(college_id=college_id)
            courses = courses.filter(college_id=college_id)
            students = students.filter(course__college_id=college_id)

        if course_id:
            students = students.filter(course_id=course_id)

        if company_id:
            supervisors = supervisors.filter(company_id=company_id)
        else:
            supervisors = supervisors.order_by("first_name", "last_name", "email")

        return Response(
            {
                "students": CustomUserSerializer(students, many=True).data,
                "academic_supervisors": CustomUserSerializer(academics, many=True).data,
                "workplace_supervisors": CustomUserSerializer(supervisors, many=True).data,
                "colleges": CollegeSerializer(colleges, many=True).data,
                "courses": CourseSerializer(courses, many=True).data,
                "companies": CompanySerializer(
                    Company.objects.annotate(
                        supervisor_count=Count(
                            "users", filter=Q(users__role="workplace_supervisor")
                        )
                    ).order_by("name"),
                    many=True,
                ).data,
            }
        )

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def cancel(self, request, pk=None):
        if request.user.role != "admin":
            raise PermissionDenied("Only admins can cancel placements.")

        placement = self.get_object()
        confirmed = request.data.get("confirm")
        if confirmed not in [True, "true", "True", 1, "1"]:
            raise ValidationError(
                {"confirm": "Set confirm=true to cancel this placement."}
            )

        if placement.status == "CANCELLED":
            raise ValidationError({"detail": "This placement is already cancelled."})

        WeeklyLog.objects.filter(placement=placement).delete()
        placement.status = "CANCELLED"
        placement.save(update_fields=["status"])

        serializer = self.get_serializer(placement)
        return Response(
            {
                "message": "Placement cancelled successfully.",
                "placement": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user

        if user.role == "student" and instance.student != user:
            raise PermissionDenied("You can only view your own placements.")
        if user.role == "workplace_supervisor" and instance.workplace_supervisor != user:
            raise PermissionDenied("You can only view placements you supervise.")
        if user.role == "academic_supervisor" and instance.academic_supervisor != user:
            raise PermissionDenied("You can only view placements you supervise.")
        return super().retrieve(request, *args, **kwargs)


class CompanyViewSet(viewsets.ModelViewSet):
    queryset = Company.objects.annotate(
        supervisor_count=Count(
            "users", filter=Q(users__role="workplace_supervisor")
        )
    ).order_by("name")
    serializer_class = CompanySerializer

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        queryset = Company.objects.annotate(
            supervisor_count=Count(
                "users", filter=Q(users__role="workplace_supervisor")
            )
        ).order_by("name")
        return queryset

    def check_admin_permission(self):
        if self.request.user.role != "admin":
            raise PermissionDenied("Only admins can manage companies.")

    def create(self, request, *args, **kwargs):
        self.check_admin_permission()
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        self.check_admin_permission()
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        self.check_admin_permission()
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        raise PermissionDenied("Deleting companies is disabled.")

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def assign_supervisors(self, request, pk=None):
        """Assign workplace supervisors to a company."""
        self.check_admin_permission()
        
        company = self.get_object()
        supervisor_ids = request.data.get("supervisor_ids", [])
        
        if not isinstance(supervisor_ids, list):
            return Response(
                {"error": "supervisor_ids must be a list"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            # Get all supervisors currently assigned to this company
            current_supervisors = CustomUser.objects.filter(company=company)
            
            # Unassign them first
            for supervisor in current_supervisors:
                supervisor.company = None
                supervisor.save(update_fields=["company"])
            
            # Assign new supervisors
            new_supervisors = CustomUser.objects.filter(
                id__in=supervisor_ids, 
                role="workplace_supervisor"
            )
            
            for supervisor in new_supervisors:
                supervisor.company = company
                supervisor.save(update_fields=["company"])
            
            # Return updated company with new supervisor count
            queryset = Company.objects.annotate(
                supervisor_count=Count(
                    "users", filter=Q(users__role="workplace_supervisor")
                )
            )
            company = queryset.get(pk=pk)
            serializer = self.get_serializer(company)
            
            return Response(
                {
                    "message": "Supervisors assigned successfully.",
                    "company": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
