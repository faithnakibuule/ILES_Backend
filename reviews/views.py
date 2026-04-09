from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from logbook.models import WeeklyLog
from .serializers import ReviewActionSerializer
from rest_framework import status

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
