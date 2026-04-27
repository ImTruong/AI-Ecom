from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone

class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ('auth', '__first__'),
    ]
    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('slug', models.SlugField(blank=True, max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
                ('icon', models.CharField(default='box', max_length=50)),
            ],
            options={'db_table': 'categories', 'verbose_name_plural': 'categories'},
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=12)),
                ('image_url', models.CharField(blank=True, max_length=500)),
                ('supplier_id', models.IntegerField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='product_app.category')),
            ],
            options={'db_table': 'products'},
        ),
        # Subclasses
        migrations.CreateModel(name='Book', fields=[('product_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='product_app.product')), ('author', models.CharField(max_length=255)), ('isbn', models.CharField(max_length=20, unique=True)), ('publisher', models.CharField(max_length=255)), ('page_count', models.IntegerField(blank=True, null=True))], options={'db_table': 'products_book'}, bases=('product_app.product',)),
        migrations.CreateModel(name='Clothes', fields=[('product_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='product_app.product')), ('brand', models.CharField(max_length=100)), ('material', models.CharField(max_length=100)), ('gender', models.CharField(choices=[('Men', 'Men'), ('Women', 'Women'), ('Unisex', 'Unisex')], max_length=20))], options={'db_table': 'products_clothes'}, bases=('product_app.product',)),
        migrations.CreateModel(name='Laptop', fields=[('product_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='product_app.product')), ('cpu', models.CharField(max_length=100)), ('ram', models.IntegerField()), ('storage', models.CharField(max_length=100)), ('gpu', models.CharField(blank=True, max_length=100))], options={'db_table': 'products_laptop'}, bases=('product_app.product',)),
        migrations.CreateModel(name='Phone', fields=[('product_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='product_app.product')), ('screen_size', models.CharField(max_length=50)), ('battery', models.IntegerField()), ('camera_specs', models.CharField(max_length=255))], options={'db_table': 'products_phone'}, bases=('product_app.product',)),
        migrations.CreateModel(name='Tablet', fields=[('product_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='product_app.product')), ('screen_size', models.CharField(max_length=50)), ('os', models.CharField(max_length=50)), ('is_stylus_supported', models.BooleanField(default=False))], options={'db_table': 'products_tablet'}, bases=('product_app.product',)),
        migrations.CreateModel(name='Camera', fields=[('product_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='product_app.product')), ('resolution', models.CharField(max_length=50)), ('sensor_type', models.CharField(max_length=100)), ('lens_included', models.CharField(blank=True, max_length=255))], options={'db_table': 'products_camera'}, bases=('product_app.product',)),
        migrations.CreateModel(name='Headphone', fields=[('product_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='product_app.product')), ('type', models.CharField(choices=[('Over-ear', 'Over-ear'), ('In-ear', 'In-ear'), ('On-ear', 'On-ear')], max_length=50)), ('is_wireless', models.BooleanField(default=True)), ('noise_cancelling', models.BooleanField(default=False))], options={'db_table': 'products_headphone'}, bases=('product_app.product',)),
        migrations.CreateModel(name='Watch', fields=[('product_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='product_app.product')), ('style', models.CharField(choices=[('Analog', 'Analog'), ('Digital', 'Digital'), ('Smart', 'Smart')], max_length=50)), ('water_resistance', models.CharField(max_length=50)), ('band_material', models.CharField(max_length=100))], options={'db_table': 'products_watch'}, bases=('product_app.product',)),
        migrations.CreateModel(name='Shoe', fields=[('product_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='product_app.product')), ('size_eu', models.IntegerField()), ('material', models.CharField(max_length=100)), ('shoe_type', models.CharField(max_length=50))], options={'db_table': 'products_shoe'}, bases=('product_app.product',)),
        migrations.CreateModel(name='Furniture', fields=[('product_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='product_app.product')), ('material', models.CharField(max_length=100)), ('dimensions', models.CharField(max_length=255)), ('weight_capacity', models.CharField(blank=True, max_length=100))], options={'db_table': 'products_furniture'}, bases=('product_app.product',)),
    ]
