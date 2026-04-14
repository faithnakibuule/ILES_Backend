# dashboards/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count
from django.db.models.functions import TruncWeek
from datetime import datetime

class WorkplaceReviewActivityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != 'workplace_supervisor':
            return Response({"error": "Not authorized"}, status=403)

        # Filter review actions where this supervisor approved/reviewed a log
        # Adjust action names based on your ReviewAction.ACTION_CHOICES
        reviews = ReviewAction.objects.filter(
            action_by=user,
            action__in=['APPROVED', 'REVIEWED']   # pick the one you use
        )

        # Group by week (works on PostgreSQL and SQLite with date)
        weekly_data = (
            reviews
            .annotate(week=TruncWeek('timestamp'))
            .values('week')
            .annotate(count=Count('id'))
            .order_by('-week')[:8]
        )

        # Format for frontend (oldest first)
        result = [
            {"week": item["week"].strftime("%b %d"), "count": item["count"]}
            for item in reversed(weekly_data)
        ]
        return Response(result)