from django.urls import path
from . import views

urlpatterns = [
    path('', views.list_suppliers, name='list_suppliers'),
    path('<int:supplier_id>/', views.get_supplier, name='get_supplier'),
    path('create/', views.create_supplier, name='create_supplier'),
    path('update/<int:supplier_id>/', views.update_supplier, name='update_supplier'),
    path('delete/<int:supplier_id>/', views.delete_supplier, name='delete_supplier'),
]
