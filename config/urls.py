# config/urls.py
from django.contrib import admin
from django.urls import path, include
import django.contrib.auth.views as auth_views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from users.views import CollegeViewSet, CourseViewSet
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

# ── Lightweight health check — responds in under 1ms ──────────────────────
# Render pings this to know the app is alive
# Much faster than letting Render hit the root 404 handler
@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "success"}, status=200)

college_list = CollegeViewSet.as_view({
    'get': 'list',
    'post': 'create',
})
college_detail = CollegeViewSet.as_view({
    'get': 'retrieve',
    'put': 'update',
    'patch': 'partial_update',
    'delete': 'destroy',
})
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

    # ── Health check — used by Render and GitHub Actions keep-alive ────────
    path('api/health/', health_check, name='health-check'),

    path('api/password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('api/password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('api/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('api/reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('api/auth/', include('users.urls')),
    path('api/colleges/', college_list, name='college-list'),
    path('api/colleges/<int:pk>/', college_detail, name='college-detail'),
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
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
