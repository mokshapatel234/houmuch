# Generated by Django 5.0.1 on 2024-04-16 05:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0056_updaterequest_updateinventoryperiod_request'),
    ]

    operations = [
        migrations.AddField(
            model_name='bookinghistory',
            name='booking_id',
            field=models.CharField(editable=False, max_length=255, null=True, unique=True),
        ),
    ]
