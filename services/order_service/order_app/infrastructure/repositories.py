from django.db import transaction

from order_app.domain.repositories import OrderRepository
from order_app.domain.services import status_from_tracking_status
from order_app.models import Order, OrderItem, ShipmentTracking


class DjangoOrderRepository(OrderRepository):
    @transaction.atomic
    def create_order(self, customer_id, total_amount, discount_amount, final_amount, voucher_code, payment_method, address, items):
        order = Order.objects.create(
            customer_id=customer_id,
            total_amount=total_amount,
            discount_amount=discount_amount,
            final_amount=final_amount,
            voucher_code=voucher_code,
            payment_method=payment_method,
            shipping_address_id=address.address_id,
            shipping_full_name=address.full_name,
            shipping_phone=address.phone,
            shipping_address_line=address.address_line,
        )
        for item in items:
            OrderItem.objects.create(
                order=order,
                product_type=item.product_type,
                product_id=item.product_id,
                variant_id=item.variant_id,
                product_name=item.product_name,
                price=item.price,
                quantity=item.quantity,
            )
        return order

    def list_for_customer(self, customer_id: int):
        return Order.objects.filter(customer_id=customer_id).order_by('-created_at')

    def get_for_customer(self, order_id: int, customer_id: int):
        return Order.objects.get(id=order_id, customer_id=customer_id)

    def list_all(self):
        return Order.objects.all().order_by('-created_at')

    def update_status(self, order_id: int, status: str):
        order = Order.objects.get(id=order_id)
        order.status = status
        order.save(update_fields=['status', 'updated_at'])
        return order

    @transaction.atomic
    def add_tracking(self, order_id: int, payload: dict, actor_id=None, actor_type=''):
        order = Order.objects.get(id=order_id)
        status_value = payload.get('status')
        valid_statuses = {choice[0] for choice in ShipmentTracking.ShipmentStatus.choices}
        if status_value not in valid_statuses:
            raise ValueError('Invalid shipment status')

        event = ShipmentTracking.objects.create(
            order=order,
            status=status_value,
            location=payload.get('location', ''),
            note=payload.get('note', ''),
            carrier=payload.get('carrier', ''),
            tracking_code=payload.get('tracking_code', ''),
            created_by_user_id=actor_id,
            created_by_user_type=actor_type,
        )
        order_status = status_from_tracking_status(status_value)
        if order_status:
            order.status = order_status
            order.save(update_fields=['status', 'updated_at'])
        return event

