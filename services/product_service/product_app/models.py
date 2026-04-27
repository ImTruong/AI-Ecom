from django.db import models
from django.utils import timezone
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='box', help_text="FontAwesome icon name")

    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'categories'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    image_url = models.CharField(max_length=500, blank=True)
    supplier_id = models.IntegerField(null=True, blank=True)
    product_type = models.CharField(max_length=50, default='generic')
    attributes = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'products'

    def __str__(self):
        return self.name

    @property
    def detail(self):
        """
        Helper property to get the specific subclass instance safely.
        """
        for attr in ['book', 'clothes', 'laptop', 'phone', 'tablet', 'camera', 'headphone', 'watch', 'shoe', 'furniture']:
            try:
                sub_obj = getattr(self, attr, None)
                if sub_obj:
                    return sub_obj
            except Exception:
                continue
        return self

    def to_dict(self):
        try:
            data = {
                'id': self.id,
                'name': self.name,
                'description': self.description,
                'price': float(self.price) if self.price else 0.0,
                'image_url': self.image_url,
                'category': self.category.name if self.category else "Uncategorized",
                'category_id': self.category_id,
                'supplier_id': self.supplier_id,
                'created_at': self.created_at.isoformat() if self.created_at else None,
            }

            product_type = getattr(self, 'product_type', None)

            # Add specific fields based on subclass
            detail = self.detail
            if detail and detail != self:
                subclass_name = detail.__class__.__name__.lower()
                if not product_type or product_type == 'generic':
                    product_type = subclass_name
                
                # Get fields belonging ONLY to the subclass (not the base Product)
                base_field_names = {f.name for f in Product._meta.concrete_fields}
                for field in detail._meta.concrete_fields:
                    # Skip base fields, relation pointers, and complex objects
                    if field.name not in base_field_names and not field.is_relation:
                        try:
                            value = getattr(detail, field.name)
                            # Ensure value is a simple JSON-serializable type
                            from decimal import Decimal
                            if isinstance(value, (str, int, float, bool)) or value is None:
                                data[field.name] = value
                            elif isinstance(value, Decimal):
                                data[field.name] = float(value)
                            else:
                                # For everything else (like objects), just use string representation
                                data[field.name] = str(value)
                        except Exception:
                            pass
            if not product_type:
                product_type = 'generic'

            data['product_type'] = product_type

            attributes = self.attributes or {}
            if isinstance(attributes, dict):
                for key, value in attributes.items():
                    if key not in data:
                        data[key] = value

            # Include variants
            try:
                data['variants'] = [
                    {
                        'id': v.id,
                        'name': v.name,
                        'price_override': float(v.price_override) if v.price_override else None,
                        'stock': v.stock,
                        'sku': v.sku,
                        'image_url': v.image_url,
                        'options': v.options or {},
                        'option_values': [
                            {
                                'id': opt.attribute_value_id,
                                'attribute': opt.attribute_value.attribute.name,
                                'value': opt.attribute_value.value,
                            }
                            for opt in v.option_values.select_related('attribute_value', 'attribute_value__attribute').all()
                        ],
                    }
                    for v in self.variants.all()
                ]
            except Exception:
                data['variants'] = []
                
            return data
        except Exception as e:
            # Fallback if something goes wrong to avoid 500
            return {'id': getattr(self, 'id', 0), 'error': 'Serialization error', 'msg': str(e)}

# --- Specific Product Types (Standardized Enterprise Structure) ---

class Book(Product):
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=20, unique=True)
    publisher = models.CharField(max_length=255)
    page_count = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'products_book'

class Clothes(Product):
    brand = models.CharField(max_length=100)
    material = models.CharField(max_length=100)
    gender = models.CharField(max_length=20, choices=[('Men', 'Men'), ('Women', 'Women'), ('Unisex', 'Unisex')])

    class Meta:
        db_table = 'products_clothes'

class Laptop(Product):
    cpu = models.CharField(max_length=100)
    ram = models.IntegerField(help_text="RAM in GB")
    storage = models.CharField(max_length=100)
    gpu = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'products_laptop'

class Phone(Product):
    screen_size = models.CharField(max_length=50)
    battery = models.IntegerField(help_text="Battery capacity in mAh")
    camera_specs = models.CharField(max_length=255)

    class Meta:
        db_table = 'products_phone'

class Tablet(Product):
    screen_size = models.CharField(max_length=50)
    os = models.CharField(max_length=50)
    is_stylus_supported = models.BooleanField(default=False)

    class Meta:
        db_table = 'products_tablet'

class Camera(Product):
    resolution = models.CharField(max_length=50)
    sensor_type = models.CharField(max_length=100)
    lens_included = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'products_camera'

class Headphone(Product):
    type = models.CharField(max_length=50, choices=[('Over-ear', 'Over-ear'), ('In-ear', 'In-ear'), ('On-ear', 'On-ear')])
    is_wireless = models.BooleanField(default=True)
    noise_cancelling = models.BooleanField(default=False)

    class Meta:
        db_table = 'products_headphone'

class Watch(Product):
    style = models.CharField(max_length=50, choices=[('Analog', 'Analog'), ('Digital', 'Digital'), ('Smart', 'Smart')])
    water_resistance = models.CharField(max_length=50)
    band_material = models.CharField(max_length=100)

    class Meta:
        db_table = 'products_watch'

class Shoe(Product):
    size_eu = models.IntegerField()
    material = models.CharField(max_length=100)
    shoe_type = models.CharField(max_length=50, help_text="Sneaker, Boots, Formal, etc.")

    class Meta:
        db_table = 'products_shoe'

class Furniture(Product):
    material = models.CharField(max_length=100)
    dimensions = models.CharField(max_length=255, help_text="LxWxH")
    weight_capacity = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = 'products_furniture'


# --- Product Variants ---

class Attribute(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        db_table = 'attributes'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class AttributeValue(models.Model):
    attribute = models.ForeignKey(Attribute, related_name='values', on_delete=models.CASCADE)
    value = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, blank=True)

    class Meta:
        db_table = 'attribute_values'
        unique_together = [['attribute', 'value']]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.attribute.name}-{self.value}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    price_override = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock = models.IntegerField(default=0)
    sku = models.CharField(max_length=100, blank=True)
    image_url = models.CharField(max_length=500, blank=True)
    options = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'product_variants'
        indexes = [
            models.Index(fields=['product']),
            models.Index(fields=['sku']),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.name}"


class ProductVariantOption(models.Model):
    variant = models.ForeignKey(ProductVariant, related_name='option_values', on_delete=models.CASCADE)
    attribute_value = models.ForeignKey(AttributeValue, related_name='variant_options', on_delete=models.CASCADE)

    class Meta:
        db_table = 'product_variant_options'
        unique_together = [['variant', 'attribute_value']]

    def __str__(self):
        return f"{self.variant_id} -> {self.attribute_value_id}"
