import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, '..', '..', 'shared'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_service.settings')
django.setup()

from authentication.models import Customer, Staff, Admin, Role, StaffRole  # noqa: E402
from outbox.service import create_outbox_event_and_save  # noqa: E402
from events.event_base import EventType  # noqa: E402


def seed_customer():
    """Create default customer account"""
    email = "client@example.com"
    password = "client123"
    
    customer, created = Customer.objects.get_or_create(
        email=email,
        defaults={
            'full_name': 'Client Demo',
            'phone': '0900000000',
            'address': '123 Demo Street, HCMC',
            'is_active': True
        }
    )
    
    if created:
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
        print(f"[Seed] Created customer: {email} / {password}")
    else:
        print(f"[Seed] Customer already exists: {email}")


def seed_staff():
    """Create default staff account"""
    email = "staff@example.com"
    password = "staff123"
    
    staff, created = Staff.objects.get_or_create(
        email=email,
        defaults={
            'full_name': 'Staff Demo',
            'phone': '0900000001',
            'role': 'staff',
            'is_active': True
        }
    )
    
    if created:
        staff.set_password(password)
        staff.save()
        
        # Assign staff role
        try:
            staff_role = Role.objects.get(name='staff')
            StaffRole.objects.get_or_create(staff=staff, role=staff_role)
        except Role.DoesNotExist:
            print(f"[Seed] Warning: 'staff' role not found")
        
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
        print(f"[Seed] Created staff: {email} / {password}")
    else:
        print(f"[Seed] Staff already exists: {email}")


def seed_admin():
    """Create default admin account (inherits from Staff)"""
    email = "admin@example.com"
    password = "admin123"
    
    # Check if admin exists
    if Admin.objects.filter(email=email).exists():
        print(f"[Seed] Admin already exists: {email}")
        return
    
    # Create admin (inherits from Staff)
    admin = Admin(
        email=email,
        full_name='Admin Super User',
        phone='0900000002',
        role='admin',
        admin_level='super',
        can_manage_users=True,
        can_manage_roles=True,
        can_manage_products=True,
        can_manage_orders=True,
        can_view_analytics=True,
        is_active=True
    )
    admin.set_password(password)
    admin.save()
    
    # Assign admin role
    try:
        admin_role = Role.objects.get(name='super_admin')
        StaffRole.objects.get_or_create(staff=admin, role=admin_role)
    except Role.DoesNotExist:
        print(f"[Seed] Warning: 'super_admin' role not found")
    
    print(f"[Seed] Created admin: {email} / {password}")


def print_credentials():
    """Print all credentials summary"""
    print("\n" + "="*60)
    print("🎉 DEFAULT ACCOUNTS CREATED SUCCESSFULLY")
    print("="*60)
    print("")
    print("📧 Customer Account:")
    print("   Email:    client@example.com")
    print("   Password: client123")
    print("")
    print("👷 Staff Account:")
    print("   Email:    staff@example.com")
    print("   Password: staff123")
    print("")
    print("🛡️  Admin Account:")
    print("   Email:    admin@example.com")
    print("   Password: admin123")
    print("")
    print("="*60)


if __name__ == "__main__":
    print("[Seed] Starting user seeding...")
    print("")
    
    seed_customer()
    seed_staff()
    seed_admin()
    
    print("")
    print_credentials()
