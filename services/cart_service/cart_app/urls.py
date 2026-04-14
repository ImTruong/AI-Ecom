"""
Cart app URLs
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.get_cart, name='get_cart'),
    path('add/', views.add_to_cart, name='add_to_cart'),
    path('update/', views.update_cart_item, name='update_cart_item'),
    path('remove/<str:product_type>/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('clear/', views.clear_cart, name='clear_cart'),
]
