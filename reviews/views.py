from django.shortcuts import render
# reviews/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from logbook.models import WeeklyLog
from .serializers import ReviewActionSerializer
from .serializers import NotificationSerializer

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