from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('product_app', '0006_rename_variant_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='productvariant',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
