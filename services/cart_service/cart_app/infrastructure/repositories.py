from django.db import transaction

from cart_app.domain.entities import CartItemInput
from cart_app.domain.repositories import CartRepository
from cart_app.models import Cart, CartItem


class DjangoCartRepository(CartRepository):
    def get_or_create_for_customer(self, customer_id: int):
        cart, _ = Cart.objects.get_or_create(customer_id=customer_id)
        return cart

    @transaction.atomic
    def add_item(self, customer_id: int, item: CartItemInput):
        cart, _ = Cart.objects.get_or_create(customer_id=customer_id)
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product_type=item.product_type,
            product_id=item.product_id,
            variant_id=item.variant_id,
            defaults={
                'price': item.price,
                'product_name': item.product_name,
                'variant_name': item.variant_name,
                'image_url': item.image_url,
                'quantity': item.quantity,
            },
        )
        if not created:
            cart_item.quantity += item.quantity
            cart_item.price = item.price
            cart_item.product_name = item.product_name or cart_item.product_name
            cart_item.variant_name = item.variant_name or cart_item.variant_name
            cart_item.image_url = item.image_url or cart_item.image_url
            cart_item.save()
        cart.refresh_from_db()
        return cart, created

    @transaction.atomic
    def update_item_quantity(self, customer_id: int, product_type: str, product_id: int, variant_id: int, quantity: int):
        cart = Cart.objects.get(customer_id=customer_id)
        cart_item = CartItem.objects.get(cart=cart, product_type=product_type, product_id=product_id, variant_id=variant_id)
        cart_item.quantity = quantity
        cart_item.save(update_fields=['quantity', 'updated_at'])
        cart.refresh_from_db()
        return cart

    @transaction.atomic
    def remove_item(self, customer_id: int, product_type: str, product_id: int, variant_id: int):
        cart = Cart.objects.get(customer_id=customer_id)
        CartItem.objects.get(cart=cart, product_type=product_type, product_id=product_id, variant_id=variant_id).delete()
        cart.refresh_from_db()
        return cart

    @transaction.atomic
    def clear(self, customer_id: int):
        cart = Cart.objects.get(customer_id=customer_id)
        cart.items.all().delete()
        cart.refresh_from_db()
        return cart

