import os
import sys
import json
import django
from decimal import Decimal
from django.utils import timezone
from django.db import connection

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..', '..'))

sys.path.append(BASE_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'product_service_config.settings')
django.setup()

from product_app.models import Attribute, AttributeValue, Product, ProductVariant, ProductVariantOption  # noqa: E402
from product_app.models import Category  # noqa: E402
from django.utils.text import slugify

DEFAULT_SEED_FILE = os.path.join(REPO_ROOT, 'seed_data.sql')
CONTAINER_SEED_FILE = '/seed_data.sql'
SEED_FILE = os.getenv('PRODUCT_SEED_FILE', DEFAULT_SEED_FILE)

ICON_MAP = {
    'Programming': 'book',
    'Self-Help': 'book',
    'T-Shirt': 'shirt',
    'Hoodie': 'shirt',
    'Accessories': 'tag',
}

REQUIRED_PRODUCT_TYPES = [
    ('electronic', 'Electronic Demo', 'Electronic product sample', 'bolt', Decimal('1500000')),
    ('clothes', 'Clothes Demo', 'Clothes product sample', 'shirt', Decimal('299000')),
    ('book', 'Book Demo', 'Book product sample', 'book', Decimal('180000')),
    ('furniture', 'Furniture Demo', 'Furniture product sample', 'chair', Decimal('2500000')),
    ('cosmetic', 'Cosmetic Demo', 'Cosmetic product sample', 'spa', Decimal('220000')),
    ('food', 'Food Demo', 'Food product sample', 'utensils', Decimal('99000')),
    ('toy', 'Toy Demo', 'Toy product sample', 'puzzle-piece', Decimal('149000')),
    ('sport_equipment', 'Sport Equipment Demo', 'Sport equipment sample', 'dumbbell', Decimal('450000')),
    ('shoes', 'Shoes Demo', 'Shoes product sample', 'shoe-prints', Decimal('650000')),
    ('accessory', 'Accessory Demo', 'Accessory product sample', 'gem', Decimal('129000')),
]


def _parse_value(raw):
    value = raw.strip()
    if not value:
        return None
    upper = value.upper()
    if upper == 'NULL':
        return None
    if upper == 'NOW()':
        return timezone.now()
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    try:
        if '.' in value:
            return Decimal(value)
        return int(value)
    except Exception:
        return value


def _split_fields(row):
    fields = []
    current = []
    in_quote = False
    i = 0
    while i < len(row):
        ch = row[i]
        if ch == "'":
            if in_quote and i + 1 < len(row) and row[i + 1] == "'":
                current.append("'")
                i += 1
            else:
                in_quote = not in_quote
                current.append(ch)
        elif ch == ',' and not in_quote:
            fields.append(''.join(current).strip())
            current = []
        else:
            current.append(ch)
        i += 1
    if current:
        fields.append(''.join(current).strip())
    return fields


def _extract_tuples(values_block):
    tuples = []
    depth = 0
    in_quote = False
    current = []
    i = 0
    while i < len(values_block):
        ch = values_block[i]
        if ch == "'":
            if in_quote and i + 1 < len(values_block) and values_block[i + 1] == "'":
                current.append("'")
                i += 1
            else:
                in_quote = not in_quote
                current.append(ch)
        elif ch == '(' and not in_quote:
            depth += 1
            if depth == 1:
                current = []
            else:
                current.append(ch)
        elif ch == ')' and not in_quote:
            depth -= 1
            if depth == 0:
                tuples.append(''.join(current))
                current = []
            else:
                current.append(ch)
        else:
            if depth >= 1:
                current.append(ch)
        i += 1
    return tuples


def _extract_values_blocks(sql_text, table_name):
    blocks = []
    marker = f"INSERT INTO {table_name}"
    start = 0
    while True:
        idx = sql_text.find(marker, start)
        if idx == -1:
            break
        segment = sql_text[idx:]
        values_idx = segment.find("VALUES")
        if values_idx == -1:
            break
        segment = segment[values_idx + len("VALUES"):]
        end_idx = segment.find("ON CONFLICT")
        if end_idx == -1:
            end_idx = segment.find(";")
        if end_idx == -1:
            break
        blocks.append(segment[:end_idx].strip())
        start = idx + len(marker)
    return blocks


def seed_categories(values_block):
    rows = _extract_tuples(values_block)
    for row in rows:
        fields = _split_fields(row)
        if len(fields) < 3:
            continue
        cid = _parse_value(fields[0])
        name = _parse_value(fields[1])
        description = _parse_value(fields[2])
        icon = ICON_MAP.get(name, 'box')
        Category.objects.update_or_create(
            id=cid,
            defaults={
                'name': name,
                'description': description or '',
                'icon': icon,
            }
        )


def seed_products(values_block):
    rows = _extract_tuples(values_block)
    for row in rows:
        fields = _split_fields(row)
        if len(fields) < 11:
            continue
        pid = _parse_value(fields[0])
        name = _parse_value(fields[1])
        description = _parse_value(fields[2])
        price = _parse_value(fields[3])
        raw_type = _parse_value(fields[4])
        product_type = str(raw_type).lower() if raw_type else 'generic'
        category_id = _parse_value(fields[5])
        image_url = _parse_value(fields[6])
        supplier_id = _parse_value(fields[7])
        raw_attrs = _parse_value(fields[8])
        is_active = bool(_parse_value(fields[9]))

        attributes = {}
        if isinstance(raw_attrs, str) and raw_attrs.strip():
            try:
                attributes = json.loads(raw_attrs)
            except json.JSONDecodeError:
                attributes = {}

        category, _ = Category.objects.get_or_create(
            id=category_id,
            defaults={'name': f'Category {category_id}', 'description': ''}
        )

        Product.objects.update_or_create(
            id=pid,
            defaults={
                'name': name,
                'description': description or '',
                'price': price or Decimal('0'),
                'product_type': product_type or 'generic',
                'category': category,
                'image_url': image_url or '',
                'supplier_id': supplier_id,
                'attributes': attributes,
                'is_active': is_active,
            }
        )


def seed_default_variants():
    color = get_or_create_attribute('Color')
    size = get_or_create_attribute('Size')
    black, _ = AttributeValue.objects.get_or_create(attribute=color, value='Black')
    red, _ = AttributeValue.objects.get_or_create(attribute=color, value='Red')
    xl, _ = AttributeValue.objects.get_or_create(attribute=size, value='XL')
    xxl, _ = AttributeValue.objects.get_or_create(attribute=size, value='XXL')

    product = Product.objects.filter(product_type='clothes').order_by('id').first()
    if not product:
        return

    combinations = [
        ('Black / XL', black, xl, 20),
        ('Black / XXL', black, xxl, 12),
        ('Red / XL', red, xl, 15),
        ('Red / XXL', red, xxl, 8),
    ]
    for name, color_value, size_value, stock in combinations:
        variant, _ = ProductVariant.objects.update_or_create(
            product=product,
            sku=f'{product.id}-{color_value.value.upper()}-{size_value.value.upper()}',
            defaults={
                'name': name,
                'price_override': product.price,
                'stock': stock,
                'image_url': product.image_url,
                'options': {'Color': color_value.value, 'Size': size_value.value},
            }
        )
        ProductVariantOption.objects.get_or_create(variant=variant, attribute_value=color_value)
        ProductVariantOption.objects.get_or_create(variant=variant, attribute_value=size_value)


def get_or_create_attribute(name):
    slug = slugify(name)
    attribute = Attribute.objects.filter(slug=slug).first() or Attribute.objects.filter(name__iexact=name).first()
    if attribute:
        return attribute
    return Attribute.objects.create(name=name)


def seed_required_product_types():
    for index, (product_type, name, description, icon, price) in enumerate(REQUIRED_PRODUCT_TYPES, start=9001):
        category, _ = Category.objects.get_or_create(
            name=name.replace(' Demo', ''),
            defaults={'description': description, 'icon': icon},
        )
        Product.objects.get_or_create(
            product_type=product_type,
            name=name,
            defaults={
                'description': description,
                'price': price,
                'category': category,
                'image_url': '',
                'supplier_id': 1,
                'attributes': {'seed_type': product_type},
                'is_active': True,
            },
        )


def reset_primary_key_sequences():
    tables = ['categories', 'products', 'attributes', 'attribute_values', 'product_variants', 'product_variant_options']
    with connection.cursor() as cursor:
        for table in tables:
            cursor.execute(
                """
                SELECT setval(
                    pg_get_serial_sequence(%s, 'id'),
                    COALESCE((SELECT MAX(id) FROM %s), 1),
                    true
                )
                """ % ("%s", table),
                [table],
            )


def seed_fallback_variants_for_all_products():
    default_attr, _ = Attribute.objects.get_or_create(name='Default')
    default_value, _ = AttributeValue.objects.get_or_create(attribute=default_attr, value='Standard')
    for product in Product.objects.filter(is_active=True):
        if product.variants.exists():
            continue
        variant, _ = ProductVariant.objects.get_or_create(
            product=product,
            sku=f'{product.id}-STANDARD',
            defaults={
                'name': 'Standard',
                'price_override': product.price,
                'stock': 50,
                'image_url': product.image_url,
                'options': {'Default': 'Standard'},
            },
        )
        ProductVariantOption.objects.get_or_create(variant=variant, attribute_value=default_value)


def main():
    seed_path = SEED_FILE
    if not os.path.exists(seed_path) and os.path.exists(CONTAINER_SEED_FILE):
        seed_path = CONTAINER_SEED_FILE
    if not os.path.exists(seed_path):
        print(f"[Seed] Missing seed file: {seed_path}")
        return

    with open(seed_path, 'r', encoding='utf-8') as f:
        sql_text = f.read()

    category_blocks = _extract_values_blocks(sql_text, 'categories')
    product_blocks = _extract_values_blocks(sql_text, 'products')

    if not category_blocks or not product_blocks:
        print("[Seed] No product data found in seed file.")
        return

    seed_categories(category_blocks[0])
    for block in product_blocks:
        seed_products(block)
    reset_primary_key_sequences()
    seed_required_product_types()
    seed_default_variants()
    seed_fallback_variants_for_all_products()
    print("[Seed] Product seeding complete.")


if __name__ == "__main__":
    main()
