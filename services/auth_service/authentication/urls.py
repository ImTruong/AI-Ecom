"""Authentication URLs"""
from django.urls import path
from . import views

urlpatterns = [
    path('customer/register/', views.customer_register, name='customer_register'),
    path('customer/login/', views.customer_login, name='customer_login'),
    path('staff/login/', views.staff_login, name='staff_login'),
    path('token/refresh/', views.token_refresh, name='token_refresh'),
    path('token/verify/', views.token_verify, name='token_verify'),
]
