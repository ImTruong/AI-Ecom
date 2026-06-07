from decimal import Decimal

from .entities import OrderItemSnapshot
from .exceptions import OrderValidationError


def ensure_cart_has_items(items: list[OrderItemSnapshot]):
    if not items:
        raise OrderValidationError('Cart is empty')


def calculate_order_total(items: list[OrderItemSnapshot]) -> Decimal:
    return sum((item.price * item.quantity for item in items), Decimal('0'))


def calculate_final_amount(total_amount: Decimal, discount_amount: Decimal) -> Decimal:
    final_amount = total_amount - discount_amount
    return final_amount if final_amount > 0 else Decimal('0')


def status_from_tracking_status(status: str) -> str | None:
    if status == 'delivered':
        return 'delivered'
    if status in {'picked_up', 'in_transit', 'out_for_delivery'}:
        return 'shipping'
    return None

