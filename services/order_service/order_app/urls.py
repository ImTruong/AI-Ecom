from django.urls import path
from . import views

urlpatterns = [
    path('place/', views.place_order, name='place_order'),
    path('mine/', views.list_my_orders, name='list_my_orders'),
    path('<int:order_id>/', views.get_order_detail, name='get_order_detail'),
    # Staff routes
    path('staff/all/', views.list_all_orders, name='list_all_orders'),
    path('staff/stats/', views.get_order_stats, name='get_order_stats'),
    path('staff/update-status/', views.update_order_status, name='update_order_status'),
]
