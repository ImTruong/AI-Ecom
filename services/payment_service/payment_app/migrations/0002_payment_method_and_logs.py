from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('payment_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=50, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('provider', models.CharField(blank=True, max_length=100)),
                ('is_online', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'db_table': 'payment_methods',
            },
        ),
        migrations.AddField(
            model_name='payment',
            name='method',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='payments', to='payment_app.paymentmethod'),
        ),
        migrations.CreateModel(
            name='PaymentLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(blank=True, max_length=100)),
                ('event_type', models.CharField(max_length=100)),
                ('request_payload', models.JSONField(blank=True, default=dict)),
                ('response_payload', models.JSONField(blank=True, default=dict)),
                ('status_code', models.IntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='logs', to='payment_app.payment')),
            ],
            options={
                'db_table': 'payment_logs',
            },
        ),
        migrations.AddIndex(
            model_name='paymentlog',
            index=models.Index(fields=['payment'], name='payment_log_payment_idx'),
        ),
        migrations.AddIndex(
            model_name='paymentlog',
            index=models.Index(fields=['provider', 'event_type'], name='payment_log_provider_event_idx'),
        ),
    ]
