# Generated by Django 5.0.1 on 2024-03-16 12:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0045_remove_updateinventoryperiod_common_amenities_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='updateinventoryperiod',
            name='num_of_rooms',
            field=models.IntegerField(default=0, verbose_name='Num Of Rooms'),
        ),
    ]
