# config/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/admin/', include('users.admin_urls')),
    path('api/placements/', include('placements.urls')),
    path('api/dashboards/', include('dashboards.urls')),
    path('api/logbook/', include('logbook.urls')),
    path('api/reviews/', include('reviews.urls')),
]

