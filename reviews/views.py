from django.shortcuts import render
# reviews/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework.decorators import action
from logbook.models import WeeklyLog
from .serializers import ReviewActionSerializer
from .serializers import NotificationSerializer, EvaluationSerializer
from .models import Notification, Evaluation
from rest_framework.exceptions import PermissionDenied, ValidationError


class ReviewHistoryView(APIView):
    """
    Returns the full audit trail for a single log.
    GET /api/logs/{id}/history/
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, log_id):
        # Step 1 — fetch the log or return 404
        try:
            log = WeeklyLog.objects.get(id=log_id)
        except WeeklyLog.DoesNotExist:
            return Response({'error': 'Log not found.'}, status=404)

        # Step 2 — get all review actions oldest first
        actions = log.logbook_review_actions.all().order_by('timestamp')

        # Step 3 — serialize and return
        serializer = ReviewActionSerializer(actions, many=True)
        return Response(serializer.data)


class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer

    #every user only ever sees their own notifications
    def get_queryset(self):
        return Notification.objects.filter(
            recipient = self.request.user
        ).order_by('-created_at')
    
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

        #Academic supervisors see the evaluations they created
        if user.role == 'academic_supervisor':
            return Evaluation.objects.filter(academic_supervisor=user)
        
        #Students see evaluations for their own logs
        if user.role == 'student':
            return Evaluation.objects.filter(log__intern=user)
        
        #Admins see everything
        if user.role == 'admin':
            return Evaluation.objects.all()
        
        return Evaluation.objects.none()
    
    def perform_create(self, serializer):
        user = self.request.user

        #Only academic supervisors can create evaluations
        if user.role != 'academic_supervisor':
            raise PermissionDenied("Only academic supervisors can create evaluations.")
        
        #get the log being evaluated
        log_id = self.request.data.get('log_id')
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
        evaluation = serializer.save(academic_supervisor=user, log=log)

        #transition log to APPROVED 
        log.status = 'APPROVED'
        log.save()



        

    

