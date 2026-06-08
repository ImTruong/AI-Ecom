from product_app.application.dto import product_input_from_payload
from product_app.domain.exceptions import VariantValidationError
from product_app.domain.services import effective_variant_price, validate_variant_combinations
from product_app.infrastructure.repositories import DjangoProductRepository


def save_product_from_payload(payload):
    product_input = product_input_from_payload(payload)
    required_attributes = product_input.attributes.get('variant_attribute_names')
    if not isinstance(required_attributes, list):
        required_attributes = None
    validate_variant_combinations(product_input.variants, required_attributes)
    return DjangoProductRepository().save(product_input)
