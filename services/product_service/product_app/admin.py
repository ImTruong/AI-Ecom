from django.contrib import admin
from .models import (
    Category, Product, Book, Clothes, Laptop, Phone, Tablet, 
    Camera, Headphone, Watch, Shoe, Furniture
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon')
    prepopulated_fields = {'slug': ('name',)}

class BaseProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description')

@admin.register(Product)
class ProductAdmin(BaseProductAdmin):
    pass

@admin.register(Book)
class BookAdmin(BaseProductAdmin):
    list_display = BaseProductAdmin.list_display + ('author', 'isbn')

@admin.register(Clothes)
class ClothesAdmin(BaseProductAdmin):
    list_display = BaseProductAdmin.list_display + ('brand', 'gender')

@admin.register(Laptop)
class LaptopAdmin(BaseProductAdmin):
    list_display = BaseProductAdmin.list_display + ('cpu', 'ram', 'storage')

@admin.register(Phone)
class PhoneAdmin(BaseProductAdmin):
    list_display = BaseProductAdmin.list_display + ('screen_size', 'battery')

@admin.register(Tablet)
class TabletAdmin(BaseProductAdmin):
    list_display = BaseProductAdmin.list_display + ('os',)

@admin.register(Camera)
class CameraAdmin(BaseProductAdmin):
    list_display = BaseProductAdmin.list_display + ('resolution',)

@admin.register(Headphone)
class HeadphoneAdmin(BaseProductAdmin):
    list_display = BaseProductAdmin.list_display + ('type', 'is_wireless')

@admin.register(Watch)
class WatchAdmin(BaseProductAdmin):
    list_display = BaseProductAdmin.list_display + ('style',)

@admin.register(Shoe)
class ShoeAdmin(BaseProductAdmin):
    list_display = BaseProductAdmin.list_display + ('size_eu', 'shoe_type')

@admin.register(Furniture)
class FurnitureAdmin(BaseProductAdmin):
    list_display = BaseProductAdmin.list_display + ('material', 'dimensions')
