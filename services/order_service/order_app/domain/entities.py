from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class OrderItemSnapshot:
    product_type: str
    product_id: int
    variant_id: int | None
    variant_name: str
    image_url: str
    product_name: str
    price: Decimal
    quantity: int


@dataclass(frozen=True)
class ShippingAddressSnapshot:
    address_id: int
    full_name: str
    phone: str
    address_line: str
