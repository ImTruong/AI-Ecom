import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, '..', '..', 'shared'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'customer_service.settings')
django.setup()

from customer_app.models import Role, Permission, RolePermission, Customer  # noqa: E402


def seed_roles_and_permissions():
    roles_data = [
        ('customer', 'Regular customer'),
        ('staff', 'Store staff'),
        ('admin', 'System administrator'),
    ]
    permissions_data = [
        ('manage_users', 'View and manage user accounts'),
        ('view_orders', 'View orders'),
        ('manage_orders', 'Update order statuses'),
        ('manage_products', 'Create/edit/delete products'),
        ('manage_suppliers', 'Manage suppliers'),
        ('view_stats', 'View dashboard statistics'),
    ]

    roles = {}
    for name, desc in roles_data:
        role, _ = Role.objects.get_or_create(name=name, defaults={'description': desc})
        roles[name] = role
        print(f"[Seed] Role '{name}' created.")

    for code, desc in permissions_data:
        perm, _ = Permission.objects.get_or_create(code=code, defaults={'description': desc})
        print(f"[Seed] Permission '{code}' created.")

    role_perms = {
        'customer': ['view_orders'],
        'staff': ['view_orders', 'manage_orders', 'manage_products', 'manage_suppliers', 'view_stats'],
        'admin': ['manage_users', 'view_orders', 'manage_orders', 'manage_products', 'manage_suppliers', 'view_stats'],
    }

    for role_name, perm_codes in role_perms.items():
        role = roles.get(role_name)
        if not role:
            continue
        for code in perm_codes:
            perm = Permission.objects.filter(code=code).first()
            if perm:
                _, created = RolePermission.objects.get_or_create(role=role, permission=perm)
                if created:
                    print(f"[Seed] {role_name} -> {code}")

    # Assign admin role to admin user (auth_customer_id=3 if seeded after customer(1) and staff(2))
    admin_user = Customer.objects.filter(email='admin@example.com').first()
    if admin_user:
        if admin_user.role != 'admin':
            admin_user.role = 'admin'
            admin_user.save()
        from customer_app.models import UserRole
        admin_role = roles.get('admin')
        if admin_role:
            UserRole.objects.get_or_create(user=admin_user, role=admin_role)
        print(f"[Seed] Admin role assigned to {admin_user.email}")

    # Assign staff role
    staff_user = Customer.objects.filter(email='staff@example.com').first()
    if staff_user:
        if staff_user.role != 'staff':
            staff_user.role = 'staff'
            staff_user.save()
        staff_role = roles.get('staff')
        if staff_role:
            from customer_app.models import UserRole
            UserRole.objects.get_or_create(user=staff_user, role=staff_role)
        print(f"[Seed] Staff role assigned to {staff_user.email}")


if __name__ == '__main__':
    seed_roles_and_permissions()
