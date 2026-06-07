from abc import ABC, abstractmethod


class SupplierRepository(ABC):
    @abstractmethod
    def list(self, only_active=False, search_query=None):
        raise NotImplementedError

    @abstractmethod
    def get(self, supplier_id):
        raise NotImplementedError

    @abstractmethod
    def create(self, payload):
        raise NotImplementedError

    @abstractmethod
    def update(self, supplier_id, payload):
        raise NotImplementedError

    @abstractmethod
    def deactivate(self, supplier_id):
        raise NotImplementedError

