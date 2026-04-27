from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView


from .views import CustomTokenObtainPairView, MeView, RegisterView, UserStatsView
from rest_framework.routers import DefaultRouter

<<<<<<< HEAD
# nothing has to be registered here — each ViewSet lives in its own app's urls.py


=======

router = DefaultRouter()
router.register(r'admin/users', AdminUserViewSet, basename='admin-user')
router.register(r'placements', PlacementViewSet, basename='placement')
>>>>>>> 1f26da8d2e097f58e8dcc47b576c9af854238aba


urlpatterns =[
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('admin-stats/', UserStatsView.as_view(), name='admin_stats'),
    path('me/', MeView.as_view(), name='me'),
    
    
    
]