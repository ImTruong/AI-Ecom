from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cart_app', '0002_cartitem_image_url_cartitem_product_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='cartitem',
            name='variant_id',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='cartitem',
            name='variant_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='cartitem',
            unique_together={('cart', 'product_type', 'product_id', 'variant_id')},
        ),
    ]
