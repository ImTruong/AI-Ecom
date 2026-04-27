from django.db import migrations


def set_default_supplier(apps, schema_editor):
    Product = apps.get_model('product_app', 'Product')
    Product.objects.filter(supplier_id__isnull=True).update(supplier_id=1)


class Migration(migrations.Migration):

    dependencies = [
        ('product_app', '0003_add_product_type_and_attributes'),
    ]

    operations = [
        migrations.RunPython(set_default_supplier, migrations.RunPython.noop),
    ]
