from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/payment/', include('payment_app.urls')),
    path('api/payments/', include('payment_app.urls')),
]
