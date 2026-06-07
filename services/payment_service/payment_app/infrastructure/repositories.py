import os

from payment_app.domain.repositories import PaymentRepository
from payment_app.domain.services import is_online_method, payment_status_for_method
from payment_app.models import Payment, PaymentLog, PaymentMethod


class DjangoPaymentRepository(PaymentRepository):
    def create_payment(self, payload):
        payment_method = payload.get('payment_method', 'cod')
        method, _ = PaymentMethod.objects.get_or_create(
            code=payment_method,
            defaults={
                'name': payment_method.upper(),
                'provider': payload.get('provider', ''),
                'is_online': is_online_method(payment_method),
            },
        )
        payment = Payment.objects.create(
            order_id=payload.get('order_id'),
            amount=payload.get('amount'),
            method=method,
            payment_method=payment_method,
            status=payment_status_for_method(payment_method),
            transaction_id=f"TXN-{payload.get('order_id')}-{int(os.times()[4])}",
        )
        response_payload = {
            'transaction_id': payment.transaction_id,
            'status': payment.status,
            'provider_response': payload.get('gateway_payload', {}),
        } if method.is_online else {}
        PaymentLog.objects.create(
            payment=payment,
            provider=method.provider,
            event_type='payment_created',
            request_payload=payload,
            response_payload=response_payload,
            status=payment.status,
            status_code=201,
        )
        return payment

    def get_by_order(self, order_id):
        return Payment.objects.get(order_id=order_id)

    def list_methods(self):
        return PaymentMethod.objects.filter(is_active=True).order_by('code')

    def list_logs(self, payment_id):
        return PaymentLog.objects.filter(payment_id=payment_id).order_by('-created_at')

