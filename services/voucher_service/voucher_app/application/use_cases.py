from voucher_app.domain.exceptions import VoucherValidationError
from voucher_app.domain.repositories import VoucherRepository
from voucher_app.domain.services import calculate_discount, voucher_is_valid


class VoucherUseCases:
    def __init__(self, repository: VoucherRepository):
        self.repository = repository

    def list_active(self):
        return self.repository.list_active_global()

    def validate(self, customer_id, code, order_amount):
        voucher = self.repository.get_by_code(str(code).strip().upper())
        if not voucher_is_valid(voucher, float(order_amount)):
            raise VoucherValidationError('Voucher is not valid for this order amount')
        if not voucher.is_global and self.repository.customer_used(voucher, customer_id):
            raise VoucherValidationError('You have already used this voucher')
        discount = calculate_discount(voucher, float(order_amount))
        return voucher, discount

    def create(self, payload):
        return self.repository.create(payload)

