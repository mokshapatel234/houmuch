# Generated by Django 5.0.1 on 2024-01-18 09:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0002_alter_customer_address_alter_customer_email_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='device_id',
            field=models.CharField(default=None, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='customer',
            name='fcm_token',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
