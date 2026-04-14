from django.db import models
from django.utils import timezone

class SearchHistory(models.Model):
    customer_id = models.IntegerField(null=True, blank=True, db_index=True)
    query = models.CharField(max_length=500)
    session_id = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'search_history'
        verbose_name_plural = 'search histories'

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'query': self.query,
            'timestamp': self.timestamp.isoformat(),
        }

class ProductView(models.Model):
    customer_id = models.IntegerField(null=True, blank=True, db_index=True)
    product_id = models.IntegerField()
    product_type = models.CharField(max_length=50)
    session_id = models.CharField(max_length=255, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'product_views'

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'product_id': self.product_id,
            'product_type': self.product_type,
            'timestamp': self.timestamp.isoformat(),
        }

class CartAction(models.Model):
    ACTION_TYPES = [
        ('add', 'Add to Cart'),
        ('remove', 'Remove from Cart'),
        ('update', 'Update Quantity'),
    ]
    customer_id = models.IntegerField(null=True, blank=True, db_index=True)
    product_id = models.IntegerField()
    product_type = models.CharField(max_length=50)
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'cart_actions'

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'product_id': self.product_id,
            'product_type': self.product_type,
            'action_type': self.action_type,
            'quantity': self.quantity,
            'timestamp': self.timestamp.isoformat(),
        }

class PurchaseAction(models.Model):
    customer_id = models.IntegerField(db_index=True)
    product_id = models.IntegerField()
    product_type = models.CharField(max_length=50)
    order_id = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=1)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'purchase_actions'

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'product_id': self.product_id,
            'product_type': self.product_type,
            'order_id': self.order_id,
            'price': str(self.price),
            'quantity': self.quantity,
            'timestamp': self.timestamp.isoformat(),
        }
