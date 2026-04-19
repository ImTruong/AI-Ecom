from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('categories/', views.category_list, name='category_list'),
    path('manage/', views.manage_product, name='manage_product'),
    path('manage/delete/<int:pk>/', views.delete_product_manage, name='delete_product_manage'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    path('variant/<int:variant_id>/stock/', views.get_variant_stock, name='variant_stock'),
    path('update-stock/', views.update_stock, name='update_stock'),
]
