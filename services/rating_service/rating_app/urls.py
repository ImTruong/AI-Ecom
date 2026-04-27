from django.urls import path
from . import views

urlpatterns = [
    path('add/', views.add_rating, name='add_rating'),
    path('list/', views.list_all_ratings, name='list_all_ratings'),
    path('product/<str:product_type>/<int:product_id>/', views.get_product_ratings, name='get_product_ratings'),
    path('order/<int:order_id>/', views.get_order_ratings, name='get_order_ratings'),
]
