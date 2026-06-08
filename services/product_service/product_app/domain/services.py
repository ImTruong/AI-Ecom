from .entities import ProductVariantInput, VariantOption
from .exceptions import VariantValidationError


def validate_variant_combinations(
    variants: list[ProductVariantInput],
    required_attributes: list[str] | None = None,
) -> list[str]:
    required_attributes = [attr for attr in (required_attributes or []) if attr]
    if not variants:
        if required_attributes:
            raise VariantValidationError('Product variants are required for selected attributes')
        return []

    required_attributes = required_attributes or _required_attributes(variants)
    if not required_attributes:
        raise VariantValidationError('Variants require option_values with product attributes')

    seen_combinations = set()
    for index, variant in enumerate(variants, start=1):
        option_attributes = [option.attribute for option in variant.option_values]

        duplicates = {attr for attr in option_attributes if option_attributes.count(attr) > 1}
        if duplicates:
            raise VariantValidationError(
                f"Variant #{index} has duplicate attributes: {', '.join(sorted(duplicates))}"
            )

        missing = set(required_attributes) - set(option_attributes)
        extra = set(option_attributes) - set(required_attributes)
        if missing or extra:
            details = []
            if missing:
                details.append(f"missing {', '.join(sorted(missing))}")
            if extra:
                details.append(f"unexpected {', '.join(sorted(extra))}")
            raise VariantValidationError(f"Variant #{index} has invalid attribute combo: {'; '.join(details)}")

        combination = tuple(
            (option.attribute, option.value)
            for option in sorted(variant.option_values, key=lambda item: item.attribute)
        )
        if combination in seen_combinations:
            raise VariantValidationError(f"Variant #{index} duplicates another variant combination")
        seen_combinations.add(combination)

    return required_attributes


def _required_attributes(variants: list[ProductVariantInput]) -> list[str]:
    required = []
    for variant in variants:
        for option in variant.option_values:
            if option.attribute not in required:
                required.append(option.attribute)
    return required


def effective_variant_price(variant):
    return variant.price_override if variant.price_override is not None else variant.product.price
