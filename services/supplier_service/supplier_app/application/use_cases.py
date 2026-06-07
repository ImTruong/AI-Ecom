from supplier_app.domain.repositories import SupplierRepository
from supplier_app.domain.services import validate_supplier_payload


class SupplierUseCases:
    def __init__(self, repository: SupplierRepository):
        self.repository = repository

    def list_suppliers(self, only_active=False, search_query=None):
        return self.repository.list(only_active=only_active, search_query=search_query)

    def get_supplier(self, supplier_id):
        return self.repository.get(supplier_id)

    def create_supplier(self, payload):
        validate_supplier_payload(payload)
        return self.repository.create(payload)

    def update_supplier(self, supplier_id, payload):
        return self.repository.update(supplier_id, payload)

    def deactivate_supplier(self, supplier_id):
        return self.repository.deactivate(supplier_id)

