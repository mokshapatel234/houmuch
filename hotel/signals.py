from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Owner
# from django.core.mail import EmailMultiAlternatives
# from django.conf import settings
# from django.template.loader import render_to_string
# from hotel_app_backend.boto_utils import ses_client
from .utils import send_mail


@receiver(post_save, sender=Owner)
def notify_user(sender, instance, created, **kwargs):
    if instance.is_verified and instance.welcome_mail_sent is False:
        data = {
            "subject": f'Welcome {instance.hotel_name}',
            "email": instance.email,
            "template": "welcome_email.html",
            "context": {'hotel_name': instance.hotel_name}
        }
        response = send_mail(data)
        if response['MessageId']:
            instance.welcome_mail_sent = True
            instance.save()
