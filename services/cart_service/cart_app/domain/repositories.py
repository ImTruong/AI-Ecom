from abc import ABC, abstractmethod

from .entities import CartItemInput


class CartRepository(ABC):
    @abstractmethod
    def get_or_create_for_customer(self, customer_id: int):
        raise NotImplementedError

    @abstractmethod
    def add_item(self, customer_id: int, item: CartItemInput):
        raise NotImplementedError

    @abstractmethod
    def update_item_quantity(self, customer_id: int, product_type: str, product_id: int, variant_id: int, quantity: int):
        raise NotImplementedError

    @abstractmethod
    def remove_item(self, customer_id: int, product_type: str, product_id: int, variant_id: int):
        raise NotImplementedError

    @abstractmethod
    def clear(self, customer_id: int):
        raise NotImplementedError

