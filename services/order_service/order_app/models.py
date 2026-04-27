from django.db import models
from django.utils import timezone

class Order(models.Model):
    class OrderStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        SHIPPING = 'shipping', 'Shipping'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'

    class PaymentMethod(models.TextChoices):
        COD = 'cod', 'Cash on Delivery'
        BANKING = 'banking', 'Banking Transfer'

    customer_id = models.IntegerField(db_index=True)
    
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    final_amount = models.DecimalField(max_digits=15, decimal_places=2)
    
    voucher_code = models.CharField(max_length=50, blank=True, null=True)
    
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING
    )
    
    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        default=PaymentMethod.COD
    )
    
    shipping_address_id = models.IntegerField()
    shipping_full_name = models.CharField(max_length=255)
    shipping_phone = models.CharField(max_length=20)
    shipping_address_line = models.TextField()
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'orders'

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'total_amount': float(self.total_amount),
            'discount_amount': float(self.discount_amount),
            'final_amount': float(self.final_amount),
            'voucher_code': self.voucher_code,
            'status': self.status,
            'payment_method': self.payment_method,
            'shipping_info': {
                'full_name': self.shipping_full_name,
                'phone': self.shipping_phone,
                'address': self.shipping_address_line
            },
            'created_at': self.created_at.isoformat(),
            'items': [item.to_dict() for item in self.items.all()]
        }

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product_type = models.CharField(max_length=20) # book, clothes
    product_id = models.IntegerField()
    product_name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=15, decimal_places=2)
    quantity = models.IntegerField()

    class Meta:
        db_table = 'order_items'
        
    def to_dict(self):
        return {
            'id': self.id,
            'product_type': self.product_type,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'price': float(self.price),
            'quantity': self.quantity,
            'subtotal': float(self.price * self.quantity)
        }
