from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class CartItemInput:
    product_type: str
    product_id: int
    variant_id: int
    product_name: str
    variant_name: str
    image_url: str
    quantity: int
    price: Decimal

