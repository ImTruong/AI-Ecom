from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class VariantOption:
    attribute: str
    value: str


@dataclass(frozen=True)
class ProductVariantInput:
    name: str
    price_override: Decimal | None
    stock: int
    sku: str
    image_url: str
    options: dict
    option_values: list[VariantOption]


@dataclass(frozen=True)
class ProductInput:
    id: int | None
    name: str
    description: str
    price: Decimal
    category_id: int
    supplier_id: int | None
    image_url: str
    product_type: str
    attributes: dict
    variants: list[ProductVariantInput]

