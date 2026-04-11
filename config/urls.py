from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
<<<<<<< HEAD
    path('api/admin/', include('users.admin_urls')),  # ← add this
=======
    path('api/', include('users.urls')),
>>>>>>> 44c1104b76085927045603daef650d79be3f43a9
    path('api/placements/', include('placements.urls')),
    path('api/dashboards/', include('dashboards.urls')),
    path('api/logbook/', include('logbook.urls')),
    path('api/reviews/', include('reviews.urls')),
]