from django.db import models
from django.utils import timezone

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Base price
    product_type = models.CharField(max_length=50, db_index=True)  # 'book', 'clothes', etc.
    category_obj = models.ForeignKey(Category, related_name='products', on_delete=models.SET_NULL, null=True, blank=True)
    # Temporary field for migration if needed, but since we are doing a fresh start, we'll just use category_obj
    image_url = models.CharField(max_length=500, blank=True)
    supplier_id = models.IntegerField(null=True, blank=True)
    attributes = models.JSONField(default=dict, blank=True)  # e.g. {"author": "...", "isbn": "..."}
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'

    def __str__(self):
        return f"{self.name} ({self.product_type})"

    @property
    def category_name(self):
        return self.category_obj.name if self.category_obj else "Uncategorized"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'price': str(self.price),
            'product_type': self.product_type,
            'category': self.category_name,
            'category_id': self.category_obj_id,
            'image_url': self.image_url,
            'supplier_id': self.supplier_id,
            'attributes': self.attributes,
            'is_active': self.is_active,
            'variants': [v.to_dict() for v in self.variants.all()]
        }

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)  # e.g. "Red, XL" or "Hardcover"
    price_override = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock = models.IntegerField(default=0)
    sku = models.CharField(max_length=100, unique=True, null=True, blank=True)
    options = models.JSONField(default=dict, blank=True)  # e.g. {"color": "Red", "size": "XL"}

    class Meta:
        db_table = 'product_variants'

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': str(self.price_override) if self.price_override else str(self.product.price),
            'stock': self.stock,
            'sku': self.sku,
            'options': self.options
        }
