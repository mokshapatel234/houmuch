# Generated by Django 5.0.1 on 2024-04-05 08:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0053_bookinghistory_cancel_by_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='ownerbankingdetail',
            name='category',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='ownerbankingdetail',
            name='subcategory',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.CreateModel(
            name='BankingAddress',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('street1', models.CharField(max_length=30)),
                ('street2', models.CharField(max_length=30)),
                ('city', models.CharField(max_length=30)),
                ('state', models.CharField(max_length=30)),
                ('postal_code', models.CharField(max_length=30)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('owner_banking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='banking_address', to='hotel.ownerbankingdetail')),
            ],
        ),
    ]
