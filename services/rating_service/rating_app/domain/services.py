from .exceptions import RatingValidationError


def validate_stars(stars):
    if not (1 <= int(stars) <= 5):
        raise RatingValidationError('Stars must be between 1 and 5')


def ensure_delivered_order(order: dict):
    if order.get('status') != 'delivered':
        raise RatingValidationError('You can only rate delivered orders')


def find_order_item(order: dict, product_id, product_type, variant_id=None):
    for item in order.get('items', []):
        same_product = str(item.get('product_id')) == str(product_id) and item.get('product_type') == product_type
        same_variant = variant_id in [None, ''] or str(item.get('variant_id')) == str(variant_id)
        if same_product and same_variant:
            return item
    raise RatingValidationError('Product not found in this delivered order')

