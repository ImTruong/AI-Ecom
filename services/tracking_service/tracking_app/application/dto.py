from tracking_app.domain.entities import TrackingEventInput
from tracking_app.domain.services import normalize_event_type, require_product_id


def event_input_from_payload(payload: dict) -> TrackingEventInput:
    product_id = payload.get('product_id')
    require_product_id(product_id)
    user_id = payload.get('user_id', payload.get('customer_id'))
    return TrackingEventInput(
        event_type=normalize_event_type(payload.get('event_type') or payload.get('action_type')),
        product_id=int(product_id),
        user_id=int(user_id) if user_id not in [None, ''] else None,
        session_id=payload.get('session_id'),
        product_variant_id=int(payload['product_variant_id']) if payload.get('product_variant_id') not in [None, ''] else None,
        metadata=payload.get('metadata') if isinstance(payload.get('metadata'), dict) else payload,
    )

