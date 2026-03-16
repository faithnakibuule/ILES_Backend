from django.shortcuts import render
#import exceptions to handle permission issues
from rest_framework.exceptions import PermissionDenied
#import viewsets to create a viewser for the InternshipPlcement model
from rest_framework import viewsets,permissions
#import the InternshipPlacement model and the PlacementSerializer to serialize the data
from .models import InternshipPlacement
from .serializers import PlacementSerializer

class PlacementViewSet(viewsets.ModelViewSet):
    serializer_class = PlacementSerializer # Every request through this ViewSet uses PlacementSerializer
    permission_classes = [permissions.IsAuthenticated]#only logged in users can access this viewset
    
    def get_queryset(self):
        user = self.request.user#get the user making the request from the jwt token
        
        if user.role == 'admin':#admins can see all placements
            return InternshipPlacement.objects.all()
        elif user.role == 'student':#students can only see their own placements
            return InternshipPlacement.objects.filter(studemt=user)
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
        if user.role == 'student' and isinstance.student != user:
            raise PermissionDenied("You can only view your own placements.")
        elif user.role == 'workplace_supervisor' and instance.workplace_supervisor != user:
            raise PermissionDenied("You can only view placements you supervise.")
        elif user.role == 'academic_supervisor' and instance.academic_supervisor != user:
            raise PermissionDenied("You can only view placements you supervise.")
        return super().retrieve(request, *args, **kwargs)
           