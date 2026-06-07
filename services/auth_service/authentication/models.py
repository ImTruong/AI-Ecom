"""
Authentication models for customers and staff
"""
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone


class Customer(models.Model):
    """Customer user model"""
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('staff', 'Staff'),
        ('admin', 'Admin'),
    ]
    email = models.EmailField(unique=True, db_index=True)
    password_hash = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='customer')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
            models.Index(fields=['role'], name='customers_role_2f3b99_idx'),
        ]

    def __str__(self):
        return f"Customer({self.email})"

    def set_password(self, raw_password):
        """Hash and set password"""
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        """Check if password is correct"""
        return check_password(raw_password, self.password_hash)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'address': self.address,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class Staff(models.Model):
    """Staff user model"""
    email = models.EmailField(unique=True, db_index=True)
    password_hash = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=50, default='staff')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'staff'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]

    def __str__(self):
        return f"Staff({self.email}, {self.role})"

    def set_password(self, raw_password):
        """Hash and set password"""
        self.password_hash = make_password(raw_password)

    def check_password(self, raw_password):
        """Check if password is correct"""
        return check_password(raw_password, self.password_hash)

    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }


class RefreshToken(models.Model):
    """Store refresh tokens"""
    token = models.CharField(max_length=500, unique=True, db_index=True)
    user_type = models.CharField(max_length=20)
    user_id = models.IntegerField()

    created_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    is_revoked = models.BooleanField(default=False)

    class Meta:
        db_table = 'refresh_tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user_type', 'user_id']),
        ]

    def __str__(self):
        return f"RefreshToken({self.user_type}:{self.user_id})"

    def is_valid(self):
        """Check if token is still valid"""
        return not self.is_revoked and self.expires_at > timezone.now()


class Permission(models.Model):
    """Permission model for RBAC"""
    name = models.CharField(max_length=100, unique=True)
    codename = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'permission'
        indexes = [
            models.Index(fields=['codename'], name='permissions_codename_idx'),
        ]

    def __str__(self):
        return f"Permission({self.codename})"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'codename': self.codename,
            'description': self.description,
        }


class Role(models.Model):
    """Role model for RBAC"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'role'

    def __str__(self):
        return f"Role({self.name})"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'permissions': [
                role_permission.permission.codename
                for role_permission in self.role_permissions.select_related('permission').all()
            ]
        }


class RolePermission(models.Model):
    """Many-to-many relationship between Role and Permission"""
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='permission_roles')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'role_permission'
        unique_together = ('role', 'permission')

    def __str__(self):
        return f"RolePermission({self.role.name}:{self.permission.codename})"


class StaffRole(models.Model):
    """Many-to-many relationship between Staff and Role"""
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='staff_roles')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_staffs')
    assigned_at = models.DateTimeField(default=timezone.now)
    assigned_by = models.ForeignKey(Staff, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_roles')

    class Meta:
        db_table = 'staff_roles'
        unique_together = ('staff', 'role')

    def __str__(self):
        return f"StaffRole({self.staff.email}:{self.role.name})"


class Admin(Staff):
    """Admin user - inherits from Staff with admin privileges"""
    admin_level = models.CharField(max_length=20, default='super')  # super, manager, support
    can_manage_users = models.BooleanField(default=True)
    can_manage_roles = models.BooleanField(default=True)
    can_manage_products = models.BooleanField(default=True)
    can_manage_orders = models.BooleanField(default=True)
    can_view_analytics = models.BooleanField(default=True)

    class Meta:
        db_table = 'admins'

    def __str__(self):
        return f"Admin({self.email}, level={self.admin_level})"

    def to_dict(self):
        base = super().to_dict()
        base.update({
            'type': 'admin',
            'admin_level': self.admin_level,
            'can_manage_users': self.can_manage_users,
            'can_manage_roles': self.can_manage_roles,
            'can_manage_products': self.can_manage_products,
            'can_manage_orders': self.can_manage_orders,
            'can_view_analytics': self.can_view_analytics,
        })
        return base

    def has_permission(self, codename):
        """Check if admin has a specific permission"""
        return Permission.objects.filter(
            permission_roles__role__role_staffs__staff_id=self.id,
            codename=codename,
        ).exists()


class Address(models.Model):
    """Address model - Customer can have multiple addresses"""
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='addresses')

    # Address fields
    full_name = models.CharField(max_length=255, blank=True, null=True)  # Recipient name
    phone = models.CharField(max_length=20, blank=True, null=True)
    street_address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, default='Vietnam')

    # Address type
    ADDRESS_TYPES = [
        ('home', 'Home'),
        ('work', 'Work'),
        ('other', 'Other'),
    ]
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPES, default='home')

    # Default address flag
    is_default = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'address'
        indexes = [
            models.Index(fields=['customer'], name='addresses_customer_idx'),
            models.Index(fields=['is_default'], name='addresses_default_idx'),
        ]

    def __str__(self):
        return f"Address({self.customer.email}:{self.city})"

    def to_dict(self):
        address_line = ', '.join(
            part for part in [
                self.street_address,
                self.city,
                self.state,
                self.postal_code,
                self.country,
            ]
            if part
        )
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'full_name': self.full_name or self.customer.full_name,
            'phone': self.phone or self.customer.phone,
            'street_address': self.street_address,
            'city': self.city,
            'state': self.state,
            'postal_code': self.postal_code,
            'country': self.country,
            'address_line': address_line,
            'address_type': self.address_type,
            'is_default': self.is_default,
            'is_active': self.is_active,
        }

    def save(self, *args, **kwargs):
        """If this address is set as default, unset other defaults for this customer"""
        if self.is_default:
            Address.objects.filter(customer=self.customer, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
