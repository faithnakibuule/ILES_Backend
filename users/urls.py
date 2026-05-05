from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView



from .views import CollegeViewSet, CourseViewSet, CustomTokenObtainPairView, MeView, RegisterView, UserStatsView, PasswordResetRequestView, PasswordResetConfirmView
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'colleges', CollegeViewSet, basename='college')
router.register(r'courses', CourseViewSet, basename='course')

# nothing has to be registered here — each ViewSet lives in its own app's urls.py




urlpatterns =[
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('password_reset/', PasswordResetRequestView.as_view(), name='password_reset'),
    path('password_reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('admin-stats/', UserStatsView.as_view(), name='admin_stats'),
    path('me/', MeView.as_view(), name='me'),
    path('', include(router.urls)),
    
    
    
]
