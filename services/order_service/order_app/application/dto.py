from decimal import Decimal

from order_app.domain.entities import OrderItemSnapshot, ShippingAddressSnapshot


def order_items_from_cart(cart_items: list[dict]) -> list[OrderItemSnapshot]:
    return [
        OrderItemSnapshot(
            product_type=item['product_type'],
            product_id=int(item['product_id']),
            variant_id=int(item['variant_id']) if item.get('variant_id') not in [None, ''] else None,
            product_name=item.get('product_name') or item.get('name') or f"{item['product_type']} #{item['product_id']}",
            price=Decimal(str(item['price'])),
            quantity=int(item['quantity']),
        )
        for item in cart_items
    ]


def address_from_payload(address_id: int, payload: dict) -> ShippingAddressSnapshot:
    return ShippingAddressSnapshot(
        address_id=address_id,
        full_name=payload['full_name'],
        phone=payload['phone'],
        address_line=payload.get('address_line') or payload.get('street_address'),
    )

