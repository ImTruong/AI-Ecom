from decimal import Decimal

from cart_app.domain.entities import CartItemInput
from cart_app.domain.services import normalize_product_type, require_variant, validate_cart_quantity


def cart_item_input_from_payload(payload: dict) -> CartItemInput:
    product_type = normalize_product_type(payload.get('product_type'))
    quantity = int(payload.get('quantity', 1))
    validate_cart_quantity(quantity)
    variant_id = payload.get('variant_id')
    require_variant(variant_id)
    return CartItemInput(
        product_type=product_type,
        product_id=int(payload.get('product_id')),
        variant_id=int(variant_id),
        product_name=payload.get('product_name') or payload.get('name') or '',
        variant_name=payload.get('variant_name') or '',
        image_url=payload.get('image_url') or '',
        quantity=quantity,
        price=Decimal(str(payload.get('price'))),
    )

