from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Owner
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from hotel_app_backend.boto_utils import ses_client

@receiver(post_save, sender=Owner)
def notify_user(sender, instance, created, **kwargs):
    if instance.is_verified and instance.welcome_mail_sent is False:
        subject = f'Welcome {instance.hotel_name}'
        html_message = render_to_string('welcome_email.html', {'hotel_name': instance.hotel_name})
        response = ses_client.send_email(
            Source=settings.DEFAULT_FROM_EMAIL,
            Destination={
                'ToAddresses': [instance.email]
            },
            Message={
                'Subject': {
                    'Data': subject,
                },
                'Body': {
                    'Html': {
                        'Data': html_message,
                    }
                }
            }
        )

        if response['MessageId']:
            instance.welcome_mail_sent = True
            instance.save()
