from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='role',
            field=models.CharField(choices=[('customer', 'Customer'), ('staff', 'Staff'), ('admin', 'Admin')], default='customer', max_length=20),
        ),
        migrations.AddIndex(
            model_name='customer',
            index=models.Index(fields=['role'], name='customers_role_2f3b99_idx'),
        ),
    ]
