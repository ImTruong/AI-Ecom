"""
Cart admin
"""
from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('created_at', 'updated_at', 'subtotal')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_id', 'get_items_count', 'get_total', 'created_at')
    search_fields = ('customer_id',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [CartItemInline]
    
    def get_items_count(self, obj):
        return obj.items.count()
    get_items_count.short_description = 'Items'
    
    def get_total(self, obj):
        return f"${obj.get_total()}"
    get_total.short_description = 'Total'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'product_type', 'product_id', 'quantity', 'price', 'subtotal')
    list_filter = ('product_type',)
    search_fields = ('cart__customer_id',)
    readonly_fields = ('created_at', 'updated_at', 'subtotal')
