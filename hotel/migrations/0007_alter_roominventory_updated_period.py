# Generated by Django 5.0.1 on 2024-01-18 05:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0006_property_updateinventoryperiod_roominventory'),
    ]

    operations = [
        migrations.AlterField(
            model_name='roominventory',
            name='updated_period',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='property_updated_period', to='hotel.updateinventoryperiod'),
        ),
    ]
