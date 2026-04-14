from django.urls import path, include

urlpatterns = [
    path('api/tracking/', include('tracking_app.urls')),
]
