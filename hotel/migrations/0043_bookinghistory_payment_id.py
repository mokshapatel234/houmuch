# Generated by Django 5.0.1 on 2024-03-13 04:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hotel', '0042_rename_booking_id_guestdetail_booking_ratings'),
    ]

    operations = [
        migrations.AddField(
            model_name='bookinghistory',
            name='payment_id',
            field=models.CharField(max_length=20, null=True),
        ),
    ]
