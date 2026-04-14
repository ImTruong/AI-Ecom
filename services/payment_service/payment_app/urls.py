from django.urls import path
from . import views

urlpatterns = [
    path('process/', views.process_payment, name='process_payment'),
    path('status/<int:order_id>/', views.get_payment_status, name='get_payment_status'),
]
