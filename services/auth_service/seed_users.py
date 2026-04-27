import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, '..', '..', 'shared'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_service.settings')
django.setup()

from authentication.models import Customer, Staff  # noqa: E402
from outbox.service import create_outbox_event_and_save  # noqa: E402
from events.event_base import EventType  # noqa: E402


def seed_customer():
    email = "client@example.com"
    password = "client123"
    if Customer.objects.filter(email=email).exists():
        print(f"[Seed] Customer {email} already exists.")
        return

    customer = Customer(
        email=email,
        full_name="Client Demo",
        phone="0900000000",
        address="HCMC"
    )
    customer.set_password(password)
    customer.save()

    create_outbox_event_and_save(
        event_type=EventType.CUSTOMER_REGISTERED,
        aggregate_id=str(customer.id),
        data={
            'customer_id': customer.id,
            'user_id': customer.id,
            'id': customer.id,
            'email': customer.email,
            'full_name': customer.full_name,
            'phone': customer.phone,
            'address': customer.address,
        }
    )
    print(f"[Seed] Created customer {email} / {password}")


def seed_staff():
    email = "staff@example.com"
    password = "staff123"
    if Staff.objects.filter(email=email).exists():
        print(f"[Seed] Staff {email} already exists.")
        return

    staff = Staff(
        email=email,
        full_name="Staff Demo",
        phone="0900000001",
        role="staff"
    )
    staff.set_password(password)
    staff.save()

    create_outbox_event_and_save(
        event_type=EventType.STAFF_CREATED,
        aggregate_id=str(staff.id),
        data={
            'staff_id': staff.id,
            'user_id': staff.id,
            'id': staff.id,
            'email': staff.email,
            'full_name': staff.full_name,
            'phone': staff.phone,
            'role': staff.role,
        }
    )
    print(f"[Seed] Created staff {email} / {password}")


if __name__ == "__main__":
    seed_customer()
    seed_staff()
