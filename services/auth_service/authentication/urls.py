"""Authentication URLs"""
from django.urls import path
from . import views

urlpatterns = [
    path('customer/register/', views.customer_register, name='customer_register'),
    path('customer/login/', views.customer_login, name='customer_login'),
    path('staff/login/', views.staff_login, name='staff_login'),
    path('token/refresh/', views.token_refresh, name='token_refresh'),
    path('token/verify/', views.token_verify, name='token_verify'),

    # Unified customer/user APIs kept under /api/customer/* for FE compatibility.
    path('profile/', views.customer_profile, name='customer_profile'),
    path('profile/update/', views.update_customer_profile, name='update_customer_profile'),
    path('address/', views.list_addresses, name='list_addresses'),
    path('address/add/', views.add_address, name='add_address'),
    path('address/delete/<int:address_id>/', views.delete_address, name='delete_address'),
    path('address/set-default/<int:address_id>/', views.set_default_address, name='set_default_address'),
    path('staff/stats/', views.customer_stats, name='customer_stats'),
    path('staff/toggle-status/<int:user_id>/', views.admin_toggle_customer_status_compat, name='admin_toggle_customer_status_compat'),
    path('<int:user_id>/', views.admin_customer_detail_compat, name='admin_customer_detail_compat'),
    
    # Admin user management APIs
    path('admin/users/', views.admin_list_users, name='admin_list_users'),
    path('admin/users/<int:user_id>/', views.admin_get_user, name='admin_get_user'),
    path('admin/users/create/', views.admin_create_staff, name='admin_create_staff'),
    path('admin/users/<int:user_id>/update/', views.admin_update_user, name='admin_update_user'),
    path('admin/users/<int:user_id>/delete/', views.admin_delete_user, name='admin_delete_user'),
    path('admin/roles/', views.admin_list_roles, name='admin_list_roles'),
    path('admin/permissions/', views.admin_list_permissions, name='admin_list_permissions'),
]
