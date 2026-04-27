"""Authentication URLs"""
from django.urls import path
from . import views

urlpatterns = [
    path('customer/register/', views.customer_register, name='customer_register'),
    path('customer/login/', views.customer_login, name='customer_login'),
    path('staff/login/', views.staff_login, name='staff_login'),
    path('token/refresh/', views.token_refresh, name='token_refresh'),
    path('token/verify/', views.token_verify, name='token_verify'),
    
    # Admin user management APIs
    path('admin/users/', views.admin_list_users, name='admin_list_users'),
    path('admin/users/<int:user_id>/', views.admin_get_user, name='admin_get_user'),
    path('admin/users/create/', views.admin_create_staff, name='admin_create_staff'),
    path('admin/users/<int:user_id>/update/', views.admin_update_user, name='admin_update_user'),
    path('admin/users/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),
    path('admin/roles/', views.admin_list_roles, name='admin_list_roles'),
    path('admin/permissions/', views.admin_list_permissions, name='admin_list_permissions'),
]
