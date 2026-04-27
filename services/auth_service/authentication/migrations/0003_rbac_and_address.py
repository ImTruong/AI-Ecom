from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0002_add_user_role'),
    ]

    operations = [
        # Create Permission model
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('codename', models.CharField(max_length=100, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'db_table': 'permissions',
            },
        ),
        migrations.AddIndex(
            model_name='permission',
            index=models.Index(fields=['codename'], name='permissions_codename_idx'),
        ),
        
        # Create Role model
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'db_table': 'roles',
            },
        ),
        
        # Create RolePermission model (many-to-many)
        migrations.CreateModel(
            name='RolePermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('permission', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='permission_roles', to='authentication.permission')),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='role_permissions', to='authentication.role')),
            ],
            options={
                'db_table': 'role_permissions',
                'unique_together': {('role', 'permission')},
            },
        ),
        
        # Create StaffRole model (many-to-many between Staff and Role)
        migrations.CreateModel(
            name='StaffRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assigned_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('assigned_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_roles', to='authentication.staff')),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='role_staffs', to='authentication.role')),
                ('staff', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='staff_roles', to='authentication.staff')),
            ],
            options={
                'db_table': 'staff_roles',
                'unique_together': {('staff', 'role')},
            },
        ),
        
        # Create Admin model (inherits from Staff)
        migrations.CreateModel(
            name='Admin',
            fields=[
                ('staff_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='authentication.staff')),
                ('admin_level', models.CharField(default='super', max_length=20)),
                ('can_manage_users', models.BooleanField(default=True)),
                ('can_manage_roles', models.BooleanField(default=True)),
                ('can_manage_products', models.BooleanField(default=True)),
                ('can_manage_orders', models.BooleanField(default=True)),
                ('can_view_analytics', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'admins',
            },
            bases=('authentication.staff',),
        ),
        
        # Create Address model
        migrations.CreateModel(
            name='Address',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(blank=True, max_length=255, null=True)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('street_address', models.TextField()),
                ('city', models.CharField(max_length=100)),
                ('state', models.CharField(blank=True, max_length=100, null=True)),
                ('postal_code', models.CharField(blank=True, max_length=20, null=True)),
                ('country', models.CharField(default='Vietnam', max_length=100)),
                ('address_type', models.CharField(choices=[('home', 'Home'), ('work', 'Work'), ('other', 'Other')], default='home', max_length=10)),
                ('is_default', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='addresses', to='authentication.customer')),
            ],
            options={
                'db_table': 'addresses',
            },
        ),
        migrations.AddIndex(
            model_name='address',
            index=models.Index(fields=['customer'], name='addresses_customer_idx'),
        ),
        migrations.AddIndex(
            model_name='address',
            index=models.Index(fields=['is_default'], name='addresses_default_idx'),
        ),
    ]
