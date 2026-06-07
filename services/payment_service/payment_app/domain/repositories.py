from abc import ABC, abstractmethod


class PaymentRepository(ABC):
    @abstractmethod
    def create_payment(self, payload):
        raise NotImplementedError

    @abstractmethod
    def get_by_order(self, order_id):
        raise NotImplementedError

    @abstractmethod
    def list_methods(self):
        raise NotImplementedError

    @abstractmethod
    def list_logs(self, payment_id):
        raise NotImplementedError

