from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/', include('placements.urls')),
    path('api/dashboards/', include('dashboards.urls')),
    path('api/', include('logbook.urls')),
]
