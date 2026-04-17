from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework.decorators import action
from logbook.models import WeeklyLog
from .serializers import ReviewActionSerializer
from rest_framework import status
from .serializers import NotificationSerializer, EvaluationSerializer
from .models import Notification, Evaluation
from rest_framework.exceptions import PermissionDenied, ValidationError


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response({"message": "Notifications will be here"})
    
class MarkNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, pk):
        return Response(
            {"message": f"Notification {pk} marked as read"},
            status = status.HTTP_200_OK
        )
class ReviewHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, log_id):
        try:
            log = WeeklyLog.objects.get(id=log_id)
        except WeeklyLog.DoesNotExist:
            return Response({'error': 'Log not found.'}, status=404)

        actions = log.logbook_review_actions.all().order_by('timestamp')

        serializer = ReviewActionSerializer(actions, many=True)
        return Response(serializer.data)


class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    #every user only ever sees their own notifications
    def get_queryset(self):
        return(
            Notification.objects
            .select_related('recipient')
            .filter(recipient = self.request.user)
            .order_by('-created_at')
        )
    
    # PATCH -mark a notification as read
    @action(detail=True, methods=['patch'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status':'mark as read'})
    
    #POST - mark all notifications as read
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response({'status':'all notifications marked as read'})
    
class EvaluationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = EvaluationSerializer

    def get_queryset(self):
        user = self.request.user

        base = (
            Evaluation.objects
            .select_related(
                'log',
                'log__intern',
                'log__placement',
                'academic_supervisor',
            )
        )

        #Academic supervisors see the evaluations they created
        if user.role == 'academic_supervisor':
            return base.filter(academic_supervisor=user)
        
        #Students see evaluations for their own logs
        if user.role == 'student':
            return base.filter(log__intern=user)
        
        #Admins see everything
        if user.role == 'admin':
            return base.all()
        
        return Evaluation.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user

        #Only academic supervisors can create evaluations
        if user.role != 'academic_supervisor':
            raise PermissionDenied("Only academic supervisors can create evaluations.")
        
        #get the log being evaluated
        log_id = self.request.data.get('log')
        try:
            log = WeeklyLog.objects.get(id=log_id)
        except WeeklyLog.DoesNotExist:
            raise ValidationError("Log not found.")
        
        #Log must be in reviewed state not submitted or draft
        if log.status != 'REVIEWED':
            raise ValidationError(
                f"Log must be in REVIEWED state to be scored. Current status: {log.status}"
                )
        
        #save the evaluation
        evaluation = serializer.save(academic_supervisor=user)

        #transition log to APPROVED 
        log = evaluation.log
        log.status = 'APPROVED'
        log.save()





        

    

