from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('customer_app', '0002_shippingaddress'),
    ]

    operations = [
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'db_table': 'roles',
            },
        ),
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True)),
            ],
            options={
                'db_table': 'permissions',
            },
        ),
        migrations.CreateModel(
            name='RolePermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('permission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customer_app.permission')),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customer_app.role')),
            ],
            options={
                'db_table': 'role_permissions',
                'unique_together': {('role', 'permission')},
            },
        ),
        migrations.CreateModel(
            name='UserRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customer_app.role')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='customer_app.customer')),
            ],
            options={
                'db_table': 'user_roles',
                'unique_together': {('user', 'role')},
            },
        ),
        migrations.AddField(
            model_name='customer',
            name='role',
            field=models.CharField(choices=[('customer', 'Customer'), ('staff', 'Staff'), ('admin', 'Admin')], default='customer', max_length=20),
        ),
    ]
