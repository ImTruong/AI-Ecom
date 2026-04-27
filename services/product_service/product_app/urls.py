from django.urls import path
from . import views

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    path('categories/', views.category_list, name='category_list'),
    path('update-stock/', views.update_stock, name='update_stock'),
    
    # Management endpoints (Staff only)
    path('manage/', views.manage_product, name='manage_product'),
    path('manage/<int:pk>/', views.delete_product_manage, name='delete_product_manage'),
    
    # Attribute management endpoints
    path('attributes/', views.list_attributes, name='list_attributes'),
    path('attributes/create/', views.create_attribute, name='create_attribute'),
    path('attributes/<int:attribute_id>/delete/', views.delete_attribute, name='delete_attribute'),
    path('attributes/<int:attribute_id>/values/', views.create_attribute_value, name='create_attribute_value'),
    path('attribute-values/<int:value_id>/delete/', views.delete_attribute_value, name='delete_attribute_value'),
    path('<int:product_id>/required-attributes/', views.get_product_required_attributes, name='get_product_required_attributes'),
]
