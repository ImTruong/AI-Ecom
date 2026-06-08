from product_app.application.dto import product_input_from_payload
from product_app.domain.repositories import ProductRepository
from product_app.domain.services import validate_variant_combinations


class ProductUseCases:
    def __init__(self, repository: ProductRepository):
        self.repository = repository

    def list_products(self, category_slug=None, search_query=None):
        return self.repository.list_active(category_slug=category_slug, search_query=search_query)

    def get_product(self, product_id: int):
        return self.repository.get_active(product_id)

    def save_product(self, payload: dict):
        product_input = product_input_from_payload(payload)
        required_attributes = product_input.attributes.get('variant_attribute_names')
        if not isinstance(required_attributes, list):
            required_attributes = None
        validate_variant_combinations(product_input.variants, required_attributes)
        return self.repository.save(product_input)

    def delete_product(self, product_id: int):
        return self.repository.delete(product_id)

    def update_stock(self, variant_id: int, quantity_delta: int):
        return self.repository.update_variant_stock(variant_id, quantity_delta)
