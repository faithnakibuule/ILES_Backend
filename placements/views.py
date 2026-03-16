from django.shortcuts import render

# placements/views.py
# Contains the view that handles GET /api/placements/my/
# Returns the active placement for the authenticated student.

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import InternshipPlacement
from .serializers import PlacementSerializer


class MyPlacementView(APIView):
    # IsAuthenticated means: only logged-in users can call this endpoint.
    # If no valid token is sent, Django returns 401 automatically.
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # request.user is the logged-in student — Django knows this
            # from the Bearer token sent in the request header.
            # We look for their placement where status is ACTIVE.
            placement = InternshipPlacement.objects.get(
                student=request.user,
                status='ACTIVE'
            )
            serializer = PlacementSerializer(placement)
            return Response(serializer.data)

        except InternshipPlacement.DoesNotExist:
            # No active placement found for this student
            return Response(
                {'detail': 'No active placement found.'},
                status=status.HTTP_404_NOT_FOUND
            )

# Create your views here.
