from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.core), # Fixed from admin.site.urls for Django-safe-typing if any, but standard is urls
    path('api/chatbot/', include('chatbot_app.urls')),
]
