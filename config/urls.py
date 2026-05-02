from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('api/password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('api/reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('api/reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    path('api/auth/', include('users.urls')),
    path('api/admin/', include('users.admin_urls')),
    path('api/placements/', include('placements.urls')),
    path('api/dashboards/', include('dashboards.urls')),
    path('api/logbook/', include('logbook.urls')),
    path('api/reviews/', include('reviews.urls')),
    path('api/', include('dashboards.urls')),
    path('api/', include('logbook.urls')),
    path('api/', include('reviews.urls')),
    path('api/core/', include('apps.core.urls')),
]
