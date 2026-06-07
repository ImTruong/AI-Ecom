from .exceptions import TrackingValidationError


VALID_EVENT_TYPES = {'AddToCart', 'ClickProduct', 'PlaceOrder'}


def normalize_event_type(value: str) -> str:
    aliases = {
        'add_to_cart': 'AddToCart',
        'add': 'AddToCart',
        'click_product': 'ClickProduct',
        'view': 'ClickProduct',
        'place_order': 'PlaceOrder',
        'purchase': 'PlaceOrder',
    }
    normalized = aliases.get(str(value or '').strip(), str(value or '').strip())
    if normalized not in VALID_EVENT_TYPES:
        raise TrackingValidationError('Invalid event_type')
    return normalized


def require_product_id(product_id):
    if product_id in [None, '']:
        raise TrackingValidationError('product_id is required')

