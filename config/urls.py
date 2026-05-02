# config/urls.py

from django.contrib import admin
from django.urls import path, include
from users.views import CourseViewSet

course_list = CourseViewSet.as_view({
    'get': 'list',
    'post': 'create',
})
course_detail = CourseViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy',
})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/courses/', course_list, name='course-list'),
    path('api/courses/<int:pk>/', course_detail, name='course-detail'),
    path('api/admin/', include('users.admin_urls')),
    path('api/placements/', include('placements.urls')),
    path('api/dashboards/', include('dashboards.urls')),
    path('api/logbook/', include('logbook.urls')),
    path('api/reviews/', include('reviews.urls')),
    path('api/', include('dashboards.urls')),
    path('api/', include('logbook.urls')),
    path('api/', include('reviews.urls')),
    path('api/', include('api.urls')),
    path('api/core/', include('apps.core.urls')),
]
