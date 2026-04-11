from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import CustomTokenObtainPairView, MeView, RegisterView, UserStatsView



urlpatterns =[
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('admin/stats/', UserStatsView.as_view(), name='admin_stats'),
    path('me/', MeView.as_view(), name='me'),
    
]