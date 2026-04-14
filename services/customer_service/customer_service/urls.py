"""
Customer Service URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def health_check(request):
    return JsonResponse({'status': 'healthy', 'service': 'customer_service'})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('api/customer/', include('customer_app.urls')),
]
