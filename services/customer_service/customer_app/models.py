from django.db import models
from django.utils import timezone

class Customer(models.Model):
    auth_customer_id = models.IntegerField(unique=True, db_index=True)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'customers'
    
    def __str__(self):
        return f"Customer({self.email})"
    
    def to_dict(self):
        return {
            'id': self.id,
            'auth_customer_id': self.auth_customer_id,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'address': self.address,
            'is_active': self.is_active,
        }

class ShippingAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='shipping_addresses')
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    address_line = models.TextField()
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'shipping_addresses'
    
    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'phone': self.phone,
            'address_line': self.address_line,
            'is_default': self.is_default
        }
