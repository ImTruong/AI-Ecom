from rating_app.domain.repositories import RatingRepository
from rating_app.models import Rating


class DjangoRatingRepository(RatingRepository):
    def exists_for_item(self, order_id, order_item_id, product_type, product_id, variant_id=None):
        query = Rating.objects.filter(order_id=order_id, product_type=product_type, product_id=product_id)
        if order_item_id:
            query = query.filter(order_item_id=order_item_id)
        if variant_id not in [None, '']:
            query = query.filter(product_variant_id=variant_id)
        return query.exists()

    def create(self, payload):
        return Rating.objects.create(**payload)

