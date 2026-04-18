from rest_framework import viewsets 
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import WeeklyLog
from reviews.models import ReviewAction
from .serializers import LogReadSerializer , LogWriteSerializer, LogReviewSerializer
from .permissions import IsWorkplaceSupervisor 
from .services import can_transition
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .filters import WeeklyLogFilter


class LogViewSet(viewsets.ModelViewSet):
    queryset = WeeklyLog.objects.all()
    serializer_class = LogReadSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = WeeklyLogFilter
    search_fields = ['intern__first_name', 'intern__last_name', 'intern__email']# Partial search: ?search=john searches intern's name and email
    ordering_fields = ['week_number', 'status', 'submitted_at']# Sorting: ?ordering=week_number or ?ordering=-week_number (descending)

    def get_queryset(self):
        user = self.request.user

        if user.role == 'admin':   
            return (
                WeeklyLog.objects
                .select_related('intern', 'placement', 'placement__workplace_supervisor')
                .prefetch_related('evaluations', 'review_actions')
                .order_by('week_number')  
            )     

        elif user.role == 'student':
            return(
                 WeeklyLog.objects
                .select_related('intern', 'placement', 'placement__workplace_supervisor')
                .prefetch_related('evaluations', 'review_actions')
                .filter(intern=user)
            )


        elif user.role == 'workplace_supervisor':
            return(
                WeeklyLog.objects
                .select_related('intern', 'placement', 'placement__workplace_supervisor')
                .prefetch_related('evaluations', 'review_actions')
                .filter(placement__workplace_supervisor=user,
                         status__in = ['SUBMITTED', 'REVIEWED', 'APPROVED'])
                .order_by('week_number')
            )
        
        elif user.role == 'academic_supervisor':
            my_students = user.supervisor_students.all()
            return(
                WeeklyLog.objects
                .select_related('intern', 'placement', 'placement__workplace_supervisor')
                .prefetch_related('evaluations', 'review_actions')
                .filter(intern__in = my_students, status='REVIEWED')
            )
    
        return WeeklyLog.objects.none()

    def get_serializer_class(self):
        # Use WriteSerializer for create/update, ReadSerializer for everything else
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
            raise ValidationError(
                "You are not allowed to make this transition."
            )
    
    @action(detail=True, methods=['post'], 
            permission_classes=[IsWorkplaceSupervisor], url_path = 'review')
    def review_log(self, request, pk=None):
        log = self.get_object()

        if log.status != 'SUBMITTED':
            raise ValidationError("Only submitted logs can be reviwed.")
        
        log.status = 'REVIEWED'
        log.save()

        ReviewAction.objects.create(
            log = log,
            action_by = request.user,
            action = 'REVIEWED',
            comment = 'Log reviewed and approved'
        )
        return Response({'message': 'Log approved and marked as REVIEWED.'})
    
   

    @action(detail=True, methods=['post'], permission_classes=[IsWorkplaceSupervisor])
    def send_back(self, request, pk=None):
        log = self.get_object()

        if not can_transition(log, 'DRAFT', request.user.role):
            raise ValidationError("You are not allowed to send this log back.")

   
        serializer = LogReviewSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        comment = serializer.validated_data['review_comment']

   
        ReviewAction.objects.create(
            log=log,
            action_by=request.user,
            action='SENT_BACK',
            comment=comment
        )

        log.status = 'DRAFT'
        log.save()

        from reviews.models import Notification
        Notification.objects.create(
            recipient = log.intern,
            message = f'Your Week {log.week_number} log  was sent back: {comment}',
            notification_type = 'LOG_SENT_BACK',
            is_read = False
        )
        return Response({'message': 'Log sent back to student for revision.'})
    
    def perform_create(self, serializer):
        serializer.save(intern=self.request.user)