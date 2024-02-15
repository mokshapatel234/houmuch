from django.db import models
from hotel_app_backend.validator import PhoneNumberRegex
from django.utils.timezone import now
# from hotel.models import ParanoidModelManager


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
    deleted_at = models.DateTimeField(blank=True, null=True, default=None, editable=False)
    # #objects = ParanoidModelManager()

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

    # def delete(self, hard=False, **kwargs):
    #     if hard:
    #         super(Customer, self).delete()
    #     else:
    #         self.deleted_at = now()
    #         self.save()

    def __str__(self):
        return self.first_name
