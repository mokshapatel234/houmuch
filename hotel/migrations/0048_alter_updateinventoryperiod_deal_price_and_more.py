# Generated by Django 5.0.1 on 2024-03-18 05:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0047_updateinventoryperiod_status_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='updateinventoryperiod',
            name='deal_price',
            field=models.IntegerField(default=0, null=True, verbose_name='Deal Price'),
        ),
        migrations.AlterField(
            model_name='updateinventoryperiod',
            name='default_price',
            field=models.IntegerField(default=0, verbose_name='Default Price'),
        ),
        migrations.AlterField(
            model_name='updateinventoryperiod',
            name='max_price',
            field=models.IntegerField(default=0, verbose_name='Max Price'),
        ),
        migrations.AlterField(
            model_name='updateinventoryperiod',
            name='min_price',
            field=models.IntegerField(default=0, verbose_name='Min Price'),
        ),
    ]
