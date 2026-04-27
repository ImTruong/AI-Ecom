from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    path('categories/', views.category_list, name='category_list'),
    
    # Management endpoints (Staff only)
    path('manage/', views.manage_product, name='manage_product'),
    path('manage/<int:pk>/', views.delete_product_manage, name='delete_product_manage'),
]
