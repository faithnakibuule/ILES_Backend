from django.shortcuts import render
# reviews/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from logbook.models import WeeklyLog
from .serializers import ReviewActionSerializer

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
