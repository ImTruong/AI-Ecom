from django.urls import path
from . import views

urlpatterns = [
    path('methods/', views.list_payment_methods, name='list_payment_methods'),
    path('process/', views.process_payment, name='process_payment'),
    path('status/<int:order_id>/', views.get_payment_status, name='get_payment_status'),
    path('<int:payment_id>/logs/', views.list_payment_logs, name='list_payment_logs'),
]
