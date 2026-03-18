from rest_framework import generics, permissions
from .models import WeeklyLog
from .serializers import LogReadSerializer

class WeeklyLogListView(generics.ListAPIView):
    """
    GET /api/logs/ -returns all weekly logs
    with overdue status included
    """
    serializer_class = LogReadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WeeklyLog.objects.select_related(
            'intern', 'placement'
        ).all()
    

