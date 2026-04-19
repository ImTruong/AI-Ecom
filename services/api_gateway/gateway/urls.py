"""
Gateway app URLs
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('cart/', views.cart_page, name='cart_page'),
    path('profile/', views.profile_page, name='profile_page'),
    path('login/', views.login_page, name='login_page'),
    path('register/', views.register_page, name='register_page'),
    path('checkout/', views.checkout_page, name='checkout_page'),
    path('orders/', views.orders_page, name='orders_page'),
    path('staff/login/', views.staff_login_page, name='staff_login_page'),
    path('staff/dashboard/', views.staff_dashboard, name='staff_dashboard'),
    path('staff/orders/', views.staff_orders, name='staff_orders'),
    path('staff/products/', views.staff_products, name='staff_products'),
    path('staff/suppliers/', views.staff_suppliers, name='staff_suppliers'),
    path('product/detail/<int:product_id>/', views.product_detail, name='product_detail'),
    path('ai-assistant/', views.ai_assistant, name='ai_assistant'),
]
