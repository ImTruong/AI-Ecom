from decimal import Decimal

from order_app.application.dto import address_from_payload, order_items_from_cart
from order_app.domain.exceptions import OrderValidationError
from order_app.domain.repositories import OrderRepository
from order_app.domain.services import calculate_final_amount, calculate_order_total, ensure_cart_has_items


class OrderUseCases:
    def __init__(self, repository: OrderRepository):
        self.repository = repository

    def create_order_from_cart(self, customer_id, cart_items, shipping_address, payment_method='cod', voucher_code=None, discount_amount=0):
        items = order_items_from_cart(cart_items)
        ensure_cart_has_items(items)
        address = address_from_payload(shipping_address['id'], shipping_address)
        total_amount = calculate_order_total(items)
        discount_amount = Decimal(str(discount_amount or 0))
        final_amount = calculate_final_amount(total_amount, discount_amount)
        return self.repository.create_order(
            customer_id=customer_id,
            total_amount=total_amount,
            discount_amount=discount_amount,
            final_amount=final_amount,
            voucher_code=voucher_code,
            payment_method=payment_method,
            address=address,
            items=items,
        )

    def list_my_orders(self, customer_id):
        return self.repository.list_for_customer(customer_id)

    def get_my_order(self, order_id, customer_id):
        return self.repository.get_for_customer(order_id, customer_id)

    def list_all_orders(self):
        return self.repository.list_all()

    def update_status(self, order_id, status):
        if status not in {'pending', 'paid', 'shipping', 'delivered', 'cancelled'}:
            raise OrderValidationError('Invalid order status')
        return self.repository.update_status(order_id, status)

    def add_tracking(self, order_id, payload, actor_id=None, actor_type=''):
        return self.repository.add_tracking(order_id, payload, actor_id=actor_id, actor_type=actor_type)

