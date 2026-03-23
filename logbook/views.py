# logbook/views.py

from rest_framework import viewsets 
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import WeeklyLog, ReviewAction 
from .serializers import LogReadSerializer , LogWriteSerializer, LogReviewSerializer
from .permissions import IsWorkplaceSupervisor 

class LogViewSet(viewsets.ModelViewSet):
    queryset = WeeklyLog.objects.all()
    serializer_class = LogReadSerializer

    def get_queryset(self):
        user = self.request.user

        if user.role == 'student':
            return WeeklyLog.objects.filter(intern=user)

        elif user.role == 'workplace_supervisor':
            return WeeklyLog.objects.filter(placement__supervisor=user)

        elif user.role == 'academic_supervisor':
            return WeeklyLog.objects.filter(status='REVIEWED')

        return WeeklyLog.objects.none()  # safety net for any other role

    def get_serializer_class(self):
        # Use WriteSerializer for create/update, ReadSerializer for everything else
        if self.action in ['create', 'update', 'partial_update']:
            return LogWriteSerializer
        return LogReadSerializer

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        log = self.get_object()

        if log.status != 'DRAFT':
            raise ValidationError("You can only submit a log that is in DRAFT status.")

        log.status = 'SUBMITTED'
        log.save()
        return Response({'message': 'Log submitted successfully.'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsWorkplaceSupervisor])
    def review_log(self, request, pk=None):
        log = self.get_object()

        if log.status != 'SUBMITTED':
            raise ValidationError("Only submitted logs can be reviwed.")
        
        log.status = 'REVIEWED'
        log.save()
        return Response({'message': 'Log approved and marked as REVIEWED.'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsWorkplaceSupervisor])
    def send_back(self, request, pk=None):
        log = self.get_object()

        if not serializer.is_valid():
            return response(serializer.errors, status=400)
        
        comment = serializer.validated_data['review_comment']

        ReviewAction.objects.create(
            log=log,
            supervisor=request.user,
            comment=comment
        )
        
        log.status = 'DRAFT'
        log.supervisor_comment = comment
        log.save()
        return Response({'message': 'Log sent back to student for revision'})
    
    