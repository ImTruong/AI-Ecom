import os
import sys

import django

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payment_service.settings')
django.setup()

from payment_app.models import PaymentMethod  # noqa: E402


PAYMENT_METHODS = [
    {'code': 'cod', 'name': 'Cash on Delivery', 'provider': '', 'is_online': False},
    {'code': 'banking', 'name': 'Bank Transfer', 'provider': 'manual_bank', 'is_online': True},
    {'code': 'momo', 'name': 'MoMo Wallet', 'provider': 'momo', 'is_online': True},
    {'code': 'vnpay', 'name': 'VNPay', 'provider': 'vnpay', 'is_online': True},
]


def main():
    for method in PAYMENT_METHODS:
        PaymentMethod.objects.update_or_create(
            code=method['code'],
            defaults={**method, 'is_active': True},
        )
    print('[Seed] Payment methods seeded.')


if __name__ == '__main__':
    main()
