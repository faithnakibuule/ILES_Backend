from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from placements.views import PlacementViewSet
from .views import CustomTokenObtainPairView, MeView, RegisterView, UserStatsView
from rest_framework.routers import DefaultRouter
from .views import AdminUserViewSet

router = DefaultRouter()
router.register(r'admin/users', AdminUserViewSet, basename='admin-user')
router.register(r'placements', PlacementViewSet, basename='placement')


urlpatterns =[
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('admin/stats/', UserStatsView.as_view(), name='admin_stats'),
    path('me/', MeView.as_view(), name='me'),
    path('', include(router.urls)),
    
]