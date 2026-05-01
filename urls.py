from django.urls import path
from django.contrib import admin
from users.views import WeeklyLogListView
from django.urls import path, include

urlpatterns = [
     path("api/dashboards/", include("dashboards.urls")),
    path('logs/', WeeklyLogListView.as_view(), name='weekly-logs'),
    path('admin/', admin.site.urls),
    path('api/', include('reviews.urls')),
    path('api/', include('logbook.urls')),
    path('api/', include('placements.urls')),
    path('api/auth/', include('users.urls')),
    path("api/admin/", include("users.urls")),
]