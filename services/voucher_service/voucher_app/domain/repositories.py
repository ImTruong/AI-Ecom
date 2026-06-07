from abc import ABC, abstractmethod


class VoucherRepository(ABC):
    @abstractmethod
    def list_active_global(self):
        raise NotImplementedError

    @abstractmethod
    def get_by_code(self, code: str):
        raise NotImplementedError

    @abstractmethod
    def customer_used(self, voucher, customer_id: int):
        raise NotImplementedError

    @abstractmethod
    def create(self, payload: dict):
        raise NotImplementedError

