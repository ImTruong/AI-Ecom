from rating_app.domain.exceptions import RatingValidationError
from rating_app.domain.repositories import RatingRepository
from rating_app.domain.services import ensure_delivered_order, find_order_item, validate_stars


class RatingUseCases:
    def __init__(self, repository: RatingRepository):
        self.repository = repository

    def add_rating(self, customer_id, payload, order):
        validate_stars(payload.get('stars'))
        ensure_delivered_order(order)
        if order.get('customer_id') != customer_id:
            raise PermissionError('Unauthorized access to this order')

        order_item = find_order_item(
            order,
            payload.get('product_id'),
            payload.get('product_type'),
            payload.get('product_variant_id') or payload.get('variant_id'),
        )
        order_item_id = order_item.get('id')
        variant_id = payload.get('product_variant_id') or payload.get('variant_id') or order_item.get('variant_id')
        if self.repository.exists_for_item(payload.get('order_id'), order_item_id, payload.get('product_type'), payload.get('product_id'), variant_id):
            raise RatingValidationError('You have already rated this item in this order')

        return self.repository.create({
            'order_id': payload.get('order_id'),
            'order_item_id': order_item_id,
            'customer_id': customer_id,
            'product_type': payload.get('product_type'),
            'product_id': payload.get('product_id'),
            'product_variant_id': variant_id,
            'product_name': payload.get('product_name') or order_item.get('product_name'),
            'stars': payload.get('stars'),
            'comment': payload.get('comment', ''),
        })

