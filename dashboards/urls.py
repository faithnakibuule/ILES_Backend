# dashboards/urls.py
from django.urls import path
from .views import WorkplaceReviewActivityView

urlpatterns = [
    path('workplace-review-activity/', WorkplaceReviewActivityView.as_view(), name='workplace-review-activity'),
]