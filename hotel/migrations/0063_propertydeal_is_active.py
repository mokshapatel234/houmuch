# Generated by Django 5.0.1 on 2024-05-01 10:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0062_merge_20240501_1010'),
    ]

    operations = [
        migrations.AddField(
            model_name='propertydeal',
            name='is_active',
            field=models.BooleanField(default=False),
        ),
    ]
