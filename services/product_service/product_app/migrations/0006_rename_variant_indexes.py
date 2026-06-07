from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('product_app', '0005_product_variants_and_attributes'),
    ]

    operations = [
        migrations.RenameIndex(
            model_name='productvariant',
            old_name='product_variants_product_id_idx',
            new_name='product_var_product_idx',
        ),
        migrations.RenameIndex(
            model_name='productvariant',
            old_name='product_variants_sku_idx',
            new_name='product_var_sku_idx',
        ),
    ]
