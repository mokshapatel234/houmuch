# Generated by Django 5.0.1 on 2024-03-01 11:32

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0036_remove_bathroomtype_deleted_at_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='OwnerBankingDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('phone', models.CharField(max_length=10, unique=True, validators=[django.core.validators.RegexValidator(regex='^\\+?1?\\d{10}$')])),
                ('contact_name', models.CharField(max_length=16)),
                ('type', models.CharField(max_length=16)),
                ('account_id', models.CharField(max_length=20)),
                ('legal_business_name', models.CharField(max_length=16)),
                ('business_type', models.CharField(max_length=50)),
                ('status', models.CharField(choices=[('inactive', 'inactive'), ('active', 'active')], default='active', max_length=50, verbose_name='status')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('deleted_at', models.DateTimeField(blank=True, default=None, null=True)),
                ('hotel_owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='banking_details', to='hotel.owner')),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_id', models.CharField(max_length=30)),
                ('settlements_account_number', models.CharField(max_length=30)),
                ('settlements_ifsc_code', models.CharField(max_length=30)),
                ('settlements_beneficiary_name', models.CharField(max_length=30)),
                ('tnc_accepted', models.BooleanField(default=True)),
                ('owner_banking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='banking_id', to='hotel.ownerbankingdetail')),
            ],
        ),
    ]
