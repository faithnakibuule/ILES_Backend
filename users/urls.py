from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

<<<<<<< HEAD
from .views import (
    CustomTokenObtainPairView,
    MeView,
    RegisterView,
    UserStatsView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
)
=======

from .views import CourseViewSet, CustomTokenObtainPairView, MeView, RegisterView, UserStatsView
>>>>>>> 688b13faf19d41637d5babd5a9f69b8a72265855
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
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
<<<<<<< HEAD
]
=======
    path('', include(router.urls)),
    
    
    
]
>>>>>>> 688b13faf19d41637d5babd5a9f69b8a72265855
