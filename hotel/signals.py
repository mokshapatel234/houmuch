from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Owner
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string


@receiver(post_save, sender=Owner)
def notify_user(sender, instance, created, **kwargs):
    if instance.is_verified:
        subject = f'Welcome {instance.hotel_name}'
        html_message = render_to_string('welcome_email.html', {'hotel_name': instance.hotel_name})
        from_email = settings.EMAIL_HOST_USER
        recipient_list = [instance.email]

        email = EmailMultiAlternatives(subject, body=None, from_email=from_email, to=recipient_list)
        email.attach_alternative(html_message, "text/html")
        email.send()
