from django.db import models
from django.utils import timezone

class Payment(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    order_id = models.IntegerField(db_index=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    payment_method = models.CharField(max_length=50) # cod, banking
    status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    transaction_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'payments'

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'amount': float(self.amount),
            'payment_method': self.payment_method,
            'status': self.status,
            'transaction_id': self.transaction_id,
            'created_at': self.created_at.isoformat()
        }
