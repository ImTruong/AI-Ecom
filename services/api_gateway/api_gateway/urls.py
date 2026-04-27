"""
API Gateway URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from gateway.views import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('', include('gateway.urls')),
]
