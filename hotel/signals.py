from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Owner, SubscriptionPlan, BookingHistory
from .utils import send_mail
from hotel_app_backend.utils import razorpay_client
from customer.email_utils import vendor_welcome_data
from django.utils.timezone import now


@receiver(post_save, sender=Owner)
def notify_user(sender, instance, created, **kwargs):
    if instance.is_verified and instance.welcome_mail_sent is False:
        data = vendor_welcome_data(instance)
        response = send_mail(data)
        if response['MessageId']:
            instance.welcome_mail_sent = True
            instance.save()


@receiver(post_save, sender=SubscriptionPlan)
def create_razorpay_plan(sender, instance, created, **kwargs):
    if created:
        data = {
            'period': 'monthly',
            'interval': instance.duration,
            'item': {
                'name': instance.name,
                'description': instance.description,
                'amount': instance.price * 100,
                'currency': 'INR'
            }
        }
        razorpay_plan = razorpay_client.plan.create(data=data)
        instance.razorpay_plan_id = razorpay_plan['id']
        instance.save()


@receiver(pre_save, sender=BookingHistory)
def set_booking_id(sender, instance, *args, **kwargs):
    if not instance.booking_id:
        current_year_suffix = now().year % 100
        prefix = f'I{current_year_suffix}'
        last_booking = sender.objects.filter(booking_id__startswith=prefix).order_by('booking_id').last()
        if last_booking and last_booking.booking_id:
            last_id_number = int(last_booking.booking_id[3:])
            new_id_number = last_id_number + 1
        else:
            new_id_number = 1
        instance.booking_id = f'{prefix}{new_id_number:04d}'
