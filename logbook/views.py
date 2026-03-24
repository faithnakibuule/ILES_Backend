# logbook/views.py

from rest_framework import viewsets 
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import WeeklyLog
from .serializers import LogReadSerializer, LogWriteSerializer, LogReviewSerializer
from .permissions import IsWorkplaceSupervisor
from .services import can_transition
from reviews.models import ReviewAction  # Import the correct model

class LogViewSet(viewsets.ModelViewSet):
    queryset = WeeklyLog.objects.all()
    serializer_class = LogReadSerializer

    def get_queryset(self):
        user = self.request.user

        if user.role == 'student':
            return WeeklyLog.objects.filter(intern=user)

        elif user.role == 'workplace_supervisor':
            # Assuming InternshipPlacement has a field 'workplace_supervisor'
            return WeeklyLog.objects.filter(placement__workplace_supervisor=user)

        elif user.role == 'academic_supervisor':
            return WeeklyLog.objects.filter(status='REVIEWED')

        return WeeklyLog.objects.none()  # fallback

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return LogWriteSerializer
        return LogReadSerializer

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        log = self.get_object()

        if can_transition(log, 'SUBMITTED', request.user.role):
            log.status = 'SUBMITTED'
            log.save()
            return Response({'message': 'Log submitted successfully.'})
        else:
            raise ValidationError("You are not allowed to make this transition.")

    @action(detail=True, methods=['post'], permission_classes=[IsWorkplaceSupervisor])
    def review_log(self, request, pk=None):
        log = self.get_object()

        if log.status != 'SUBMITTED':
            raise ValidationError("Only submitted logs can be reviewed.")

        # Update status
        log.status = 'REVIEWED'
        log.save()

        # Create audit trail
        ReviewAction.objects.create(
            log=log,
            action_by=request.user,
            action='APPROVED',  # or 'REVIEWED' if you prefer
            comment='Log reviewed and approved.',
        )

        return Response({'message': 'Log approved and marked as REVIEWED.'})

    @action(detail=True, methods=['post'], permission_classes=[IsWorkplaceSupervisor])
    def send_back(self, request, pk=None):
        log = self.get_object()
        serializer = LogReviewSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        comment = serializer.validated_data['review_comment']

        # Create audit trail
        ReviewAction.objects.create(
            log=log,
            action_by=request.user,
            action='SENT_BACK',
            comment=comment,
        )

        # Reset log to DRAFT and store comment
        log.status = 'DRAFT'
        log.supervisor_comment = comment
        log.save()

        return Response({'message': 'Log sent back to student for revision.'})