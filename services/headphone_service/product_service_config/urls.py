from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/products/', include('product_app.urls')),
    path('api/books/', include('product_app.urls')),
    path('api/clothes/', include('product_app.urls')),
]
