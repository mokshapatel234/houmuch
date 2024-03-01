from django.db import models
from hotel_app_backend.validator import PhoneNumberRegex


class Customer(models.Model):
    first_name = models.CharField(('First Name'), max_length=255)
    last_name = models.CharField(('Last Name'), max_length=255)
    email = models.EmailField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(validators=[PhoneNumberRegex], max_length=17, blank=True)
    profile_image = models.CharField(max_length=255, null=True, blank=True)
    address = models.TextField(verbose_name='address', null=True, blank=True)
    government_id = models.TextField(verbose_name='gov_id', null=True, blank=True)
    fcm_token = models.CharField(max_length=255, null=True, blank=True)
    device_id = models.CharField(max_length=255, default=None, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    def __str__(self):
        return self.first_name
