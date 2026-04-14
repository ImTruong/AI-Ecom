import os
import sys
import django
from datetime import datetime, timedelta

# SETUP ENVIRONMENT
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'voucher_service.settings')
django.setup()

from voucher_app.models import Voucher

def seed_vouchers():
    print("Seeding global vouchers...")
    
    vouchers = [
        {
            'code': 'WELCOME10',
            'name': 'Welcome Discount',
            'description': '10% off for all new customers!',
            'discount_type': Voucher.DiscountType.PERCENTAGE,
            'discount_value': 10,
            'min_order_value': 0,
            'is_global': True,
            'end_date': datetime.now() + timedelta(days=365)
        },
        {
            'code': 'FREESHIP',
            'name': 'Free Shipping Simulation',
            'description': '$5 off your order!',
            'discount_type': Voucher.DiscountType.FIXED,
            'discount_value': 5,
            'min_order_value': 30,
            'is_global': True,
            'end_date': datetime.now() + timedelta(days=365)
        },
        {
            'code': 'SUPER50',
            'name': 'Super Deal',
            'description': '50% off, up to $20!',
            'discount_type': Voucher.DiscountType.PERCENTAGE,
            'discount_value': 50,
            'min_order_value': 50,
            'max_discount': 20,
            'is_global': True,
            'end_date': datetime.now() + timedelta(days=30)
        }
    ]
    
    for v_data in vouchers:
        voucher, created = Voucher.objects.get_or_create(
            code=v_data['code'],
            defaults=v_data
        )
        if created:
            print(f"Created voucher: {voucher.code}")
        else:
            print(f"Voucher {voucher.code} already exists")

if __name__ == '__main__':
    seed_vouchers()
