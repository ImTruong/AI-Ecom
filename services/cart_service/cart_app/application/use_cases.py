from cart_app.application.dto import cart_item_input_from_payload
from cart_app.domain.repositories import CartRepository
from cart_app.domain.services import normalize_product_type, require_variant, validate_cart_quantity


class CartUseCases:
    def __init__(self, repository: CartRepository):
        self.repository = repository

    def get_cart(self, customer_id: int):
        return self.repository.get_or_create_for_customer(customer_id)

    def add_to_cart(self, customer_id: int, payload: dict):
        item = cart_item_input_from_payload(payload)
        return self.repository.add_item(customer_id, item)

    def update_quantity(self, customer_id: int, payload: dict):
        product_type = normalize_product_type(payload.get('product_type'))
        product_id = int(payload.get('product_id'))
        variant_id = payload.get('variant_id')
        require_variant(variant_id)
        quantity = int(payload.get('quantity'))
        validate_cart_quantity(quantity)
        return self.repository.update_item_quantity(customer_id, product_type, product_id, int(variant_id), quantity)

    def remove_from_cart(self, customer_id: int, product_type: str, product_id: int, variant_id: int):
        product_type = normalize_product_type(product_type)
        require_variant(variant_id)
        return self.repository.remove_item(customer_id, product_type, product_id, int(variant_id))

    def clear_cart(self, customer_id: int):
        return self.repository.clear(customer_id)

