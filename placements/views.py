from django.shortcuts import render
from rest_framework.exceptions import PermissionDenied
from rest_framework import viewsets,permissions
from .models import InternshipPlacement
from .serializers import PlacementSerializer


class PlacementViewSet(viewsets.ModelViewSet):
    serializer_class = PlacementSerializer # Every request through this ViewSet uses PlacementSerializer
    permission_classes = [permissions.IsAuthenticated]#only logged in users can access this viewset
    
    filterset_fields = ['status', 'company_name']#?status=ACTIVE or ?company_name=Tech
    search_fields = [
    'student__first_name',
    'student__last_name', 
    'student__email',
    'company_name',
]# ?search=john searches student name/email
    ordering_fields = ['start_date', 'end_date', 'status', 'company_name']# Sorting: ?ordering=start_date
    
    def get_queryset(self):
        user = self.request.user#get the user making the request from the jwt token
        
        if user.role == 'admin':#admins can see all placements
            return InternshipPlacement.objects.all()
        elif user.role == 'student':#students can only see their own placements
            return InternshipPlacement.objects.filter(student=user)
        elif user.role == 'workplace_supervisor':#supervisors can only see placements they supervise
            return InternshipPlacement.objects.filter(workplace_supervisor=user)
        elif user.role == 'academic_supervisor':#academic supervisors can only see placements they supervise
            return InternshipPlacement.objects.filter(academic_supervisor=user)
        else:
            return InternshipPlacement.objects.none()#other users cannot see any placements
    
    def perform_create(self, serializer):
        user = self.request.user
        if user.role != 'admin':#only admins can create placements
            raise PermissionDenied("Only admins can create placements.")
        serializer.save()
        
    def retrieve(self, request, *args, **kwargs):
        #fetch the specific placement instance being requested
        instance = self.get_object()
        user = request.user
           
        #check if the user has permission to view this placement
        if user.role == 'student' and instance.student != user:
            raise PermissionDenied("You can only view your own placements.")
        elif user.role == 'workplace_supervisor' and instance.workplace_supervisor != user:
            raise PermissionDenied("You can only view placements you supervise.")
        elif user.role == 'academic_supervisor' and instance.academic_supervisor != user:
            raise PermissionDenied("You can only view placements you supervise.")
        return super().retrieve(request, *args, **kwargs)
           

