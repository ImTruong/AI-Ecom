from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.list_active_vouchers, name='list_vouchers'),
    path('validate/', views.validate_voucher, name='validate_voucher'),
    path('create/', views.create_voucher, name='create_voucher'),
]
