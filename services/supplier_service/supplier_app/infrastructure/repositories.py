from django.db.models import Q

from supplier_app.domain.repositories import SupplierRepository
from supplier_app.models import Supplier


class DjangoSupplierRepository(SupplierRepository):
    def list(self, only_active=False, search_query=None):
        suppliers = Supplier.objects.filter(is_active=True) if only_active else Supplier.objects.all()
        if search_query:
            suppliers = suppliers.filter(
                Q(name__icontains=search_query) |
                Q(contact_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(address__icontains=search_query)
            )
        return suppliers

    def get(self, supplier_id):
        return Supplier.objects.get(id=supplier_id)

    def create(self, payload):
        return Supplier.objects.create(
            name=payload.get('name'),
            contact_name=payload.get('contact_name', ''),
            email=payload.get('email'),
            phone=payload.get('phone'),
            address=payload.get('address'),
        )

    def update(self, supplier_id, payload):
        supplier = Supplier.objects.get(id=supplier_id)
        for field in ['name', 'contact_name', 'email', 'phone', 'address', 'is_active']:
            if field in payload:
                setattr(supplier, field, payload[field])
        supplier.save()
        return supplier

    def deactivate(self, supplier_id):
        supplier = Supplier.objects.get(id=supplier_id)
        supplier.is_active = False
        supplier.save(update_fields=['is_active', 'updated_at'])
        return supplier

