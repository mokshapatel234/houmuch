# Generated by Django 5.0.1 on 2024-04-09 04:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0054_ownerbankingdetail_category_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bankingaddress',
            name='city',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='bankingaddress',
            name='state',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='bankingaddress',
            name='street1',
            field=models.CharField(max_length=255),
        ),
        migrations.AlterField(
            model_name='bankingaddress',
            name='street2',
            field=models.CharField(max_length=255),
        ),
    ]
