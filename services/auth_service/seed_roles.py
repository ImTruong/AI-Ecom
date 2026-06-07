#!/usr/bin/env python
"""
Seed script for RBAC roles and permissions
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'auth_service.settings')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

django.setup()

from authentication.models import Permission, Role, RolePermission

def seed_permissions():
    """Create default permissions"""
    permissions = [
        # User management
        {'name': 'View Users', 'codename': 'view_users', 'description': 'Can view user list'},
        {'name': 'Create User', 'codename': 'create_user', 'description': 'Can create new users'},
        {'name': 'Edit User', 'codename': 'edit_user', 'description': 'Can edit user details'},
        {'name': 'Delete User', 'codename': 'delete_user', 'description': 'Can delete users'},
        
        # Role management
        {'name': 'View Roles', 'codename': 'view_roles', 'description': 'Can view roles'},
        {'name': 'Create Role', 'codename': 'create_role', 'description': 'Can create roles'},
        {'name': 'Edit Role', 'codename': 'edit_role', 'description': 'Can edit roles'},
        {'name': 'Delete Role', 'codename': 'delete_role', 'description': 'Can delete roles'},
        
        # Product management
        {'name': 'View Products', 'codename': 'view_products', 'description': 'Can view products'},
        {'name': 'Create Product', 'codename': 'create_product', 'description': 'Can create products'},
        {'name': 'Edit Product', 'codename': 'edit_product', 'description': 'Can edit products'},
        {'name': 'Delete Product', 'codename': 'delete_product', 'description': 'Can delete products'},
        
        # Order management
        {'name': 'View Orders', 'codename': 'view_orders', 'description': 'Can view orders'},
        {'name': 'Manage Orders', 'codename': 'manage_orders', 'description': 'Can manage orders'},
        
        # Analytics
        {'name': 'View Analytics', 'codename': 'view_analytics', 'description': 'Can view analytics'},
        
        # Supplier management
        {'name': 'View Suppliers', 'codename': 'view_suppliers', 'description': 'Can view suppliers'},
        {'name': 'Manage Suppliers', 'codename': 'manage_suppliers', 'description': 'Can manage suppliers'},

        # Voucher management
        {'name': 'View Vouchers', 'codename': 'view_vouchers', 'description': 'Can view vouchers'},
        {'name': 'Manage Vouchers', 'codename': 'manage_vouchers', 'description': 'Can manage vouchers'},

        # Shipping management
        {'name': 'View Shipping', 'codename': 'view_shipping', 'description': 'Can view shipping tracking'},
        {'name': 'Manage Shipping', 'codename': 'manage_shipping', 'description': 'Can update shipping tracking'},

        # AI knowledgebase management (pending feature)
        {'name': 'View Knowledgebase', 'codename': 'view_knowledgebase', 'description': 'Can view AI knowledgebase'},
        {'name': 'Manage Knowledgebase', 'codename': 'manage_knowledgebase', 'description': 'Can manage AI knowledgebase'},
    ]
    
    created_count = 0
    for perm_data in permissions:
        perm, created = Permission.objects.get_or_create(
            codename=perm_data['codename'],
            defaults=perm_data
        )
        if created:
            created_count += 1
            print(f"  Created permission: {perm.codename}")
        else:
            print(f"  Permission exists: {perm.codename}")
    
    return created_count

def seed_roles():
    """Create default roles with permissions"""
    customer_role, created = Role.objects.get_or_create(
        name='Customer',
        defaults={
            'description': 'Customer role for storefront users',
            'is_active': True
        }
    )
    if created:
        print(f"  Created role: {customer_role.name}")
    
    # Super Admin - has all permissions
    admin_role, created = Role.objects.get_or_create(
        name='Admin',
        defaults={
            'description': 'Administrator with full access',
            'is_active': True
        }
    )
    if created:
        print(f"  Created role: {admin_role.name}")
    else:
        print(f"  Role exists: {admin_role.name}")
    
    # Add all permissions to admin
    all_perms = Permission.objects.all()
    for perm in all_perms:
        RolePermission.objects.get_or_create(role=admin_role, permission=perm)
    print(f"  Assigned {all_perms.count()} permissions to admin")
    
    # Staff role - limited permissions
    staff_role, created = Role.objects.get_or_create(
        name='Staff',
        defaults={
            'description': 'Regular staff member',
            'is_active': True
        }
    )
    if created:
        print(f"  Created role: {staff_role.name}")
    else:
        print(f"  Role exists: {staff_role.name}")
    
    # Assign limited permissions to staff
    staff_permissions = [
        'view_products', 'create_product', 'edit_product',
        'view_orders', 'manage_orders',
        'view_suppliers', 'manage_suppliers',
        'view_vouchers', 'manage_vouchers',
        'view_shipping', 'manage_shipping',
        'view_knowledgebase', 'manage_knowledgebase'
    ]
    for perm_codename in staff_permissions:
        try:
            perm = Permission.objects.get(codename=perm_codename)
            RolePermission.objects.get_or_create(role=staff_role, permission=perm)
        except Permission.DoesNotExist:
            print(f"  Warning: Permission {perm_codename} not found")

    legacy_admin_role, _ = Role.objects.get_or_create(
        name='super_admin',
        defaults={'description': 'Legacy admin role alias', 'is_active': True}
    )
    legacy_staff_role, _ = Role.objects.get_or_create(
        name='staff',
        defaults={'description': 'Legacy staff role alias', 'is_active': True}
    )
    for perm in all_perms:
        RolePermission.objects.get_or_create(role=legacy_admin_role, permission=perm)
    for perm_codename in staff_permissions:
        try:
            perm = Permission.objects.get(codename=perm_codename)
            RolePermission.objects.get_or_create(role=legacy_staff_role, permission=perm)
        except Permission.DoesNotExist:
            pass
    
    # Manager role
    manager_role, created = Role.objects.get_or_create(
        name='manager',
        defaults={
            'description': 'Manager with elevated permissions',
            'is_active': True
        }
    )
    if created:
        print(f"  Created role: {manager_role.name}")
    else:
        print(f"  Role exists: {manager_role.name}")
    
    # Assign manager permissions
    manager_permissions = [
        'view_products', 'create_product', 'edit_product', 'delete_product',
        'view_orders', 'manage_orders',
        'view_suppliers', 'manage_suppliers',
        'view_vouchers', 'manage_vouchers',
        'view_shipping', 'manage_shipping',
        'view_knowledgebase', 'manage_knowledgebase',
        'view_analytics'
    ]
    for perm_codename in manager_permissions:
        try:
            perm = Permission.objects.get(codename=perm_codename)
            RolePermission.objects.get_or_create(role=manager_role, permission=perm)
        except Permission.DoesNotExist:
            print(f"  Warning: Permission {perm_codename} not found")
    
    print(f"  Assigned {manager_role.role_permissions.count()} permissions to manager")

def main():
    print("Seeding RBAC roles and permissions...")
    print("")
    
    print("Step 1: Creating permissions...")
    perm_count = seed_permissions()
    print(f"  Created {perm_count} new permissions")
    print("")
    
    print("Step 2: Creating roles...")
    seed_roles()
    print("")
    
    print("✅ RBAC seeding complete!")
    print("")
    print("Available roles:")
    for role in Role.objects.all():
        print(f"  - {role.name}: {role.role_permissions.count()} permissions")

if __name__ == '__main__':
    main()
