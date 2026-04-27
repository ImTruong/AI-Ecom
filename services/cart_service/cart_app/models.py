"""
Cart models
"""
from django.db import models
from django.utils import timezone


class Cart(models.Model):
    """Shopping cart for a customer"""
    customer_id = models.IntegerField(db_index=True, unique=True)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'carts'
        indexes = [
            models.Index(fields=['customer_id']),
        ]
    
    def __str__(self):
        return f"Cart(customer_id={self.customer_id})"
    
    def get_total(self):
        """Calculate total price"""
        total = sum(item.subtotal for item in self.items.all())
        return total
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'items': [item.to_dict() for item in self.items.all()],
            'total': str(self.get_total()),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class CartItem(models.Model):
    """Item in a shopping cart"""
    PRODUCT_TYPE_CHOICES = [
        ('book', 'Book'),
        ('clothes', 'Clothes'),
    ]
    
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES)
    product_id = models.IntegerField()
    variant_id = models.IntegerField(null=True, blank=True)
    product_name = models.CharField(max_length=255, blank=True, null=True)
    variant_name = models.CharField(max_length=255, blank=True, null=True)
    image_url = models.CharField(max_length=500, blank=True, null=True)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cart_items'
        indexes = [
            models.Index(fields=['cart', 'product_type', 'product_id']),
        ]
        unique_together = [['cart', 'product_type', 'product_id', 'variant_id']]
    
    def __str__(self):
        return f"CartItem({self.product_type}:{self.product_id} x{self.quantity})"
    
    @property
    def subtotal(self):
        """Calculate subtotal"""
        return self.price * self.quantity
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'cart_id': self.cart_id,
            'product_type': self.product_type,
            'product_id': self.product_id,
            'variant_id': self.variant_id,
            'product_name': self.product_name,
            'variant_name': self.variant_name,
            'image_url': self.image_url,
            'quantity': self.quantity,
            'price': str(self.price),
            'subtotal': str(self.subtotal),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
