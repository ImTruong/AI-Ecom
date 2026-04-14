"""
Authentication models for customers and staff
"""
from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from django.utils import timezone


class Customer(models.Model):
    """Customer user model"""
    email = models.EmailField(unique=True, db_index=True)
    password_hash = models.CharField(max_length=255)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customers'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
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
