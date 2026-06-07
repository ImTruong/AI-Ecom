from .exceptions import CartValidationError


VALID_PRODUCT_TYPES = {
    'electronic', 'clothes', 'book', 'furniture', 'cosmetic', 'food', 'toy',
    'sport_equipment', 'shoes', 'accessory', 'laptop', 'phone', 'watch',
    'camera', 'shoe', 'tablet', 'headphone',
}


def normalize_product_type(product_type: str) -> str:
    value = str(product_type or '').strip().lower()
    aliases = {
        'books': 'book',
        'sports': 'sport_equipment',
        'sportequipment': 'sport_equipment',
        'shoe': 'shoes',
    }
    value = aliases.get(value, value.rstrip('s') if value.rstrip('s') in VALID_PRODUCT_TYPES else value)
    if value not in VALID_PRODUCT_TYPES:
        raise CartValidationError(f"Invalid product_type: {product_type}")
    return value


def validate_cart_quantity(quantity: int):
    if int(quantity) < 1:
        raise CartValidationError('Quantity must be at least 1')


def require_variant(variant_id):
    if variant_id in [None, '']:
        raise CartValidationError('variant_id is required. Cart items must point to ProductVariant.')

