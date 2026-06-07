from django.utils import timezone


def voucher_is_valid(voucher, order_value=0):
    now = timezone.now()
    if not voucher.is_active:
        return False
    if voucher.start_date > now or voucher.end_date < now:
        return False
    if voucher.usage_limit and voucher.usage_count >= voucher.usage_limit:
        return False
    if float(order_value) < float(voucher.min_order_value):
        return False
    return True


def calculate_discount(voucher, order_value):
    if voucher.discount_type == voucher.DiscountType.PERCENTAGE:
        discount = (float(voucher.discount_value) / 100) * float(order_value)
        if voucher.max_discount:
            discount = min(discount, float(voucher.max_discount))
    else:
        discount = min(float(voucher.discount_value), float(order_value))
    return discount

