from abc import ABC, abstractmethod

from .entities import ProductInput


class ProductRepository(ABC):
    @abstractmethod
    def list_active(self, category_slug=None, search_query=None):
        raise NotImplementedError

    @abstractmethod
    def get_active(self, product_id: int):
        raise NotImplementedError

    @abstractmethod
    def save(self, product_input: ProductInput):
        raise NotImplementedError

    @abstractmethod
    def delete(self, product_id: int):
        raise NotImplementedError

    @abstractmethod
    def update_variant_stock(self, variant_id: int, quantity_delta: int):
        raise NotImplementedError

