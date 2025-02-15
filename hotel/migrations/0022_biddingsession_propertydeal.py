# Generated by Django 5.0.1 on 2024-02-08 10:22

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0005_alter_customer_email_alter_customer_phone_number'),
        ('hotel', '0021_owner_category'),
    ]

    operations = [
        migrations.CreateModel(
            name='BiddingSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_open', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('deleted_at', models.DateTimeField(blank=True, default=None, editable=False, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PropertyDeal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_winning_bid', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('deleted_at', models.DateTimeField(blank=True, default=None, editable=False, null=True)),
                ('customer_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='customer_id', to='customer.customer')),
                ('property_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='property_id', to='hotel.property')),
                ('session_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='session_id', to='hotel.biddingsession')),
            ],
        ),
    ]
