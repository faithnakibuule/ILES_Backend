from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView


from .views import CustomTokenObtainPairView, MeView, RegisterView, UserStatsView
from rest_framework.routers import DefaultRouter

<<<<<<< HEAD
# nothing has to be registered here — each ViewSet lives in its own app's urls.py



=======
# Import ViewSets from other apps
from users.views import AdminUserViewSet
from placements.views import PlacementViewSet

router = DefaultRouter()
router.register(r'admin/users', AdminUserViewSet, basename='admin-user')
router.register(r'placements', PlacementViewSet, basename='placement')
>>>>>>> 145c24520eccf4c44b6f77248d6301276881a23d

urlpatterns =[
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('admin-stats/', UserStatsView.as_view(), name='admin_stats'),
    path('me/', MeView.as_view(), name='me'),
    
    
    
]