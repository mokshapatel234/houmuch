# Generated by Django 5.0.1 on 2024-01-19 10:43

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0009_remove_owner_first_name_remove_owner_last_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='owner',
            name='email',
            field=models.EmailField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='owner',
            name='phone_number',
            field=models.CharField(blank=True, max_length=17, unique=True, validators=[django.core.validators.RegexValidator(regex='^\\+?1?\\d{10}$')]),
        ),
    ]
