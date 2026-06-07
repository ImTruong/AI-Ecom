from abc import ABC, abstractmethod


class RatingRepository(ABC):
    @abstractmethod
    def exists_for_item(self, order_id, order_item_id, product_type, product_id, variant_id=None):
        raise NotImplementedError

    @abstractmethod
    def create(self, payload):
        raise NotImplementedError

