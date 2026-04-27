"""
Customer app URLs
"""
from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.get_profile, name='get_profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('address/', views.list_addresses, name='list_addresses'),
    path('address/add/', views.add_address, name='add_address'),
    path('address/delete/<int:address_id>/', views.delete_address, name='delete_address'),
    path('address/set-default/<int:address_id>/', views.set_default_address, name='set_default_address'),
    path('staff/stats/', views.get_customer_stats, name='get_customer_stats'),
]
