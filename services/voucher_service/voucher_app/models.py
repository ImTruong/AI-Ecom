from django.db import models
from django.utils import timezone

class Voucher(models.Model):
    class DiscountType(models.TextChoices):
        PERCENTAGE = 'percentage', 'Percentage'
        FIXED = 'fixed', 'Fixed Amount'

    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    discount_type = models.CharField(
        max_length=20,
        choices=DiscountType.choices,
        default=DiscountType.PERCENTAGE
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    
    usage_limit = models.IntegerField(null=True, blank=True)
    usage_count = models.IntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    is_global = models.BooleanField(default=True) # If true, any customer can use

    class Meta:
        db_table = 'vouchers'

    def __str__(self):
        return f"{self.code} ({self.discount_value})"

    def is_valid(self, order_value=0):
        now = timezone.now()
        if not self.is_active: return False
        if self.start_date > now or self.end_date < now: return False
        if self.usage_limit and self.usage_count >= self.usage_limit: return False
        if float(order_value) < float(self.min_order_value): return False
        return True

    def calculate_discount(self, order_value):
        if self.discount_type == self.DiscountType.PERCENTAGE:
            discount = (float(self.discount_value) / 100) * float(order_value)
            if self.max_discount:
                discount = min(discount, float(self.max_discount))
        else:
            discount = min(float(self.discount_value), float(order_value))
        return discount

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'discount_type': self.discount_type,
            'discount_value': float(self.discount_value),
            'min_order_value': float(self.min_order_value),
            'max_discount': float(self.max_discount) if self.max_discount else None,
            'end_date': self.end_date.isoformat(),
            'is_global': self.is_global
        }

class VoucherUsage(models.Model):
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE, related_name='usages')
    customer_id = models.IntegerField()
    order_id = models.IntegerField()
    used_at = models.DateTimeField(default=timezone.now)
    discount_applied = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'voucher_usages'
        unique_together = ('voucher', 'order_id')
