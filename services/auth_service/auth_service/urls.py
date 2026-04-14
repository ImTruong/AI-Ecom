from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # The gateway forwards /api/auth/* to this service, 
    # but it retains the full prefix if it's not stripped.
    # We should match 'api/auth/' to include authentication.urls
    path('api/auth/', include('authentication.urls')),
]
