from decimal import Decimal

from product_app.domain.entities import ProductInput, ProductVariantInput, VariantOption
from product_app.domain.exceptions import VariantValidationError


def product_input_from_payload(payload: dict) -> ProductInput:
    reserved_keys = {
        'id', 'name', 'description', 'price', 'category_id', 'supplier_id',
        'image_url', 'product_type', 'attributes', 'variants',
    }
    attributes = payload.get('attributes')
    if not isinstance(attributes, dict):
        attributes = {key: value for key, value in payload.items() if key not in reserved_keys}

    variants_payload = payload.get('variants', [])
    if not isinstance(variants_payload, list):
        variants_payload = []

    return ProductInput(
        id=payload.get('id'),
        name=payload.get('name'),
        description=payload.get('description'),
        price=Decimal(str(payload.get('price', 0))),
        category_id=payload.get('category_id'),
        supplier_id=payload.get('supplier_id'),
        image_url=payload.get('image_url', ''),
        product_type=(payload.get('product_type') or 'generic').lower(),
        attributes=attributes,
        variants=[_variant_input_from_payload(item) for item in variants_payload],
    )


def _variant_input_from_payload(payload: dict) -> ProductVariantInput:
    return ProductVariantInput(
        name=payload.get('name') or '',
        price_override=Decimal(str(payload['price_override'])) if payload.get('price_override') is not None else None,
        stock=int(payload.get('stock', 0)),
        sku=payload.get('sku', ''),
        image_url=payload.get('image_url', ''),
        is_active=payload.get('is_active', True) is not False,
        options=payload.get('options', {}) if isinstance(payload.get('options'), dict) else {},
        option_values=[_option_from_payload(item) for item in payload.get('option_values', [])],
    )


def _option_from_payload(payload: dict) -> VariantOption:
    if not isinstance(payload, dict):
        raise VariantValidationError('Each variant option must be an object')
    attribute = str(payload.get('attribute') or '').strip()
    value = str(payload.get('value') or '').strip()
    if not attribute or not value:
        raise VariantValidationError('Each variant option requires attribute and value')
    return VariantOption(attribute=attribute, value=value)
