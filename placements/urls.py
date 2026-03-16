# placements/urls.py
# Registers the URL patterns for the placements app.

from django.urls import path
from .views import MyPlacementView

urlpatterns = [
    # GET /api/placements/my/ → returns the student's active placement
    path('my/', MyPlacementView.as_view(), name='my-placement'),
]