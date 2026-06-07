from abc import ABC, abstractmethod


class OrderRepository(ABC):
    @abstractmethod
    def create_order(self, customer_id, total_amount, discount_amount, final_amount, voucher_code, payment_method, address, items):
        raise NotImplementedError

    @abstractmethod
    def list_for_customer(self, customer_id: int):
        raise NotImplementedError

    @abstractmethod
    def get_for_customer(self, order_id: int, customer_id: int):
        raise NotImplementedError

    @abstractmethod
    def list_all(self):
        raise NotImplementedError

    @abstractmethod
    def update_status(self, order_id: int, status: str):
        raise NotImplementedError

    @abstractmethod
    def add_tracking(self, order_id: int, payload: dict, actor_id=None, actor_type=''):
        raise NotImplementedError

