from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('order_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='variant_id',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name='ShipmentTracking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('created', 'Created'), ('picked_up', 'Picked Up'), ('in_transit', 'In Transit'), ('out_for_delivery', 'Out For Delivery'), ('delivered', 'Delivered'), ('failed', 'Failed'), ('returned', 'Returned')], default='created', max_length=30)),
                ('location', models.CharField(blank=True, max_length=255)),
                ('note', models.TextField(blank=True)),
                ('carrier', models.CharField(blank=True, max_length=100)),
                ('tracking_code', models.CharField(blank=True, max_length=100)),
                ('event_time', models.DateTimeField(default=django.utils.timezone.now)),
                ('created_by_user_id', models.IntegerField(blank=True, null=True)),
                ('created_by_user_type', models.CharField(blank=True, max_length=20)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shipping_events', to='order_app.order')),
            ],
            options={
                'db_table': 'shipment_tracking',
            },
        ),
        migrations.AddIndex(
            model_name='shipmenttracking',
            index=models.Index(fields=['order', 'event_time'], name='shipment_order_time_idx'),
        ),
        migrations.AddIndex(
            model_name='shipmenttracking',
            index=models.Index(fields=['status'], name='shipment_status_idx'),
        ),
    ]
