# Generated by Django 5.0.1 on 2024-03-05 09:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0039_remove_product_deleted_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='SubscriptionPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30, verbose_name='Plan')),
                ('price', models.IntegerField()),
                ('duration', models.IntegerField(choices=[(3, '3 months'), (6, '6 months'), (9, '9 months'), (12, '12 months')])),
                ('description', models.TextField(max_length=255)),
                ('razorpay_plan_id', models.CharField(blank=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
