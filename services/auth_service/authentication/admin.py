"""Admin registration for authentication models"""
from django.contrib import admin
from .models import Customer, Staff, RefreshToken


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'full_name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['email', 'full_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'full_name', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['email', 'full_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(RefreshToken)
class RefreshTokenAdmin(admin.ModelAdmin):
    list_display = ['id', 'user_type', 'user_id', 'created_at', 'expires_at', 'is_revoked']
    list_filter = ['user_type', 'is_revoked', 'created_at']
    readonly_fields = ['created_at']
