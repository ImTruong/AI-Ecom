from django.db import models
from django.utils import timezone


class PaymentMethod(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    provider = models.CharField(max_length=100, blank=True)
    is_online = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'payment_methods'

    def __str__(self):
        return self.code

    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'provider': self.provider,
            'is_online': self.is_online,
            'is_active': self.is_active,
        }


class Payment(models.Model):
    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    order_id = models.IntegerField(db_index=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT, related_name='payments', null=True, blank=True)
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
            'method': self.method.to_dict() if self.method else None,
            'status': self.status,
            'transaction_id': self.transaction_id,
            'created_at': self.created_at.isoformat()
        }


class PaymentLog(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='logs')
    provider = models.CharField(max_length=100, blank=True)
    event_type = models.CharField(max_length=100)
    request_payload = models.JSONField(default=dict, blank=True)
    response_payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=50, blank=True)
    status_code = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'payment_logs'
        indexes = [
            models.Index(fields=['payment'], name='payment_log_payment_idx'),
            models.Index(fields=['provider', 'event_type'], name='payment_log_provider_event_idx'),
        ]

    def to_dict(self):
        return {
            'id': self.id,
            'payment_id': self.payment_id,
            'provider': self.provider,
            'event_type': self.event_type,
            'request_payload': self.request_payload,
            'response_payload': self.response_payload,
            'status': self.status,
            'status_code': self.status_code,
            'created_at': self.created_at.isoformat(),
        }
