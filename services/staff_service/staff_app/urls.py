from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('login/', views.staff_login, name='staff_login'),
    # Add more staff routes here
]
