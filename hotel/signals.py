from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Owner, SubscriptionPlan
from .utils import send_mail
from hotel_app_backend.utils import razorpay_client
from customer.email_utils import vendor_welcome_data


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
