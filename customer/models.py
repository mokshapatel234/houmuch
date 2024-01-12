from django.db import models
from hotel_app_backend.validator import PhoneNumberRegex

# Create your models here.
class Customer(models.Model):
    first_name = models.CharField(('First Name'), max_length=30)
    last_name = models.CharField(('Last Name'), max_length=20)
    email = models.EmailField(max_length=100, null=True)
    phone_number = models.CharField(validators=[PhoneNumberRegex], max_length=17, blank=True)
    profile_image = models.CharField(max_length=255, null=True, blank=True)
    address = models.TextField(verbose_name='address', null=True)
    government_id = models.TextField(verbose_name='gov_id', null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True, default=None, editable=False)