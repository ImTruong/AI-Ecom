from django.db import transaction
from django.db.models import Q
from django.utils.text import slugify

from product_app.domain.entities import ProductInput
from product_app.domain.repositories import ProductRepository
from product_app.models import Attribute, AttributeValue, Product, ProductVariant, ProductVariantOption


class DjangoProductRepository(ProductRepository):
    def list_active(self, category_slug=None, search_query=None):
        products = Product.objects.filter(is_active=True)
        if category_slug:
            products = products.filter(category__slug=category_slug)
        if search_query:
            products = products.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))
        return products

    def get_active(self, product_id: int):
        return Product.objects.get(pk=product_id, is_active=True)

    @transaction.atomic
    def save(self, product_input: ProductInput):
        product = Product.objects.get(pk=product_input.id) if product_input.id else Product()
        product.name = product_input.name
        product.description = product_input.description
        product.price = product_input.price
        product.category_id = product_input.category_id
        product.supplier_id = 1 if product_input.supplier_id in [None, ''] else product_input.supplier_id
        product.image_url = product_input.image_url
        product.product_type = product_input.product_type
        product.attributes = product_input.attributes
        product.save()

        product.variants.all().delete()
        for variant in product_input.variants:
            variant_obj = ProductVariant.objects.create(
                product=product,
                name=variant.name or product.name,
                price_override=variant.price_override,
                stock=variant.stock,
                sku=variant.sku,
                image_url=variant.image_url,
                is_active=variant.is_active,
                options=variant.options,
            )
            for option in variant.option_values:
                attribute = self._get_or_create_attribute(option.attribute)
                attr_value = self._get_or_create_attribute_value(attribute, option.value)
                ProductVariantOption.objects.create(variant=variant_obj, attribute_value=attr_value)
        return product

    def delete(self, product_id: int):
        product = Product.objects.get(pk=product_id)
        product.delete()

    def update_variant_stock(self, variant_id: int, quantity_delta: int):
        variant = ProductVariant.objects.get(id=variant_id)
        new_stock = int(variant.stock) + int(quantity_delta)
        if new_stock < 0:
            raise ValueError('Insufficient variant stock')
        variant.stock = new_stock
        variant.save(update_fields=['stock'])
        return variant

    def _get_or_create_attribute(self, name):
        slug = slugify(name)
        attribute = Attribute.objects.filter(slug=slug).first() or Attribute.objects.filter(name__iexact=name).first()
        if attribute:
            return attribute
        return Attribute.objects.create(name=name)

    def _get_or_create_attribute_value(self, attribute, value):
        slug = slugify(f"{attribute.name}-{value}")
        attr_value = (
            AttributeValue.objects.filter(attribute=attribute, slug=slug).first()
            or AttributeValue.objects.filter(attribute=attribute, value__iexact=value).first()
        )
        if attr_value:
            return attr_value
        return AttributeValue.objects.create(attribute=attribute, value=value)
