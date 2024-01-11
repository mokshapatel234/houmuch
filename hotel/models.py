from django.db import models
from django.core.validators import RegexValidator
from django.utils.timezone import now


class Hotel(models.Model):
    first_name = models.CharField(('First Name'), max_length=30 , null=False)
    last_name = models.CharField(('Last Name'), max_length=20, null=False)
    email = models.EmailField(max_length=100, null=False)
    phoneNumberRegex = RegexValidator(regex = r"^\+?1?\d{10}$")
    phone_number = models.CharField(validators=[phoneNumberRegex], max_length=17, blank=True)
    profile_image = models.CharField(max_length=255, null=True)
    address = models.TextField(verbose_name='address')
    government_id = models.TextField(verbose_name='gov_id')
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    bidding_mode = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True, default=None, editable=False)

    def is_authenticated(self):
        return True  

    def is_anonymous(self):
        return False

    def delete(self, hard=False, **kwargs):
        if hard:
            super(Hotel, self).delete()
        else:
            self.deleted_at = now()
            self.save()
    
    def __str__(self):
        return self.first_name


class FCMToken(models.Model):
    user_id = models.IntegerField()
    fcm_token = models.CharField(max_length=255,null=True,blank=True)
    is_owner = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True,blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True,blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True, default=None, editable=False)

    def delete(self, hard=False, **kwargs):
        if hard:
            super(FCMToken, self).delete()
        else:
            self.deleted_at = now()
            self.save()
    
    def __str__(self):
        return self.first_name

