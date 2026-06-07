from django.utils import timezone

from voucher_app.domain.repositories import VoucherRepository
from voucher_app.models import Voucher, VoucherUsage


class DjangoVoucherRepository(VoucherRepository):
    def list_active_global(self):
        now = timezone.now()
        return Voucher.objects.filter(is_active=True, is_global=True, start_date__lte=now, end_date__gte=now)

    def get_by_code(self, code: str):
        return Voucher.objects.get(code=code)

    def customer_used(self, voucher, customer_id: int):
        return VoucherUsage.objects.filter(voucher=voucher, customer_id=customer_id).exists()

    def create(self, payload: dict):
        return Voucher.objects.create(
            code=payload.get('code').upper(),
            name=payload.get('name'),
            description=payload.get('description', ''),
            discount_type=payload.get('discount_type'),
            discount_value=payload.get('discount_value'),
            min_order_value=payload.get('min_order_value', 0),
            max_discount=payload.get('max_discount'),
            start_date=payload.get('start_date', timezone.now()),
            end_date=payload.get('end_date'),
            usage_limit=payload.get('usage_limit'),
            is_global=payload.get('is_global', True),
        )

