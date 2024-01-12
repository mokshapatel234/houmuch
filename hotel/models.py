from django.db import models
from hotel_app_backend.validator import PhoneNumberRegex
from django.utils.timezone import now


class Owner(models.Model):
    first_name = models.CharField(('First Name'), max_length=30 , null=False)
    last_name = models.CharField(('Last Name'), max_length=20, null=False)
    email = models.EmailField(max_length=100, null=False)
    phone_number = models.CharField(validators=[PhoneNumberRegex], max_length=17, blank=True)
    profile_image = models.CharField(max_length=255, null=True, blank=True)
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
            super(Owner, self).delete()
        else:
            self.deleted_at = now()
            self.save()
    
    def __str__(self):
        return self.first_name


class FCMToken(models.Model):
    user_id = models.IntegerField()
    fcm_token = models.CharField(max_length=255, null=True, blank=True)
    is_owner = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True, default=None, editable=False)

    def delete(self, hard=False, **kwargs):
        if hard:
            super(FCMToken, self).delete()
        else:
            self.deleted_at = now()
            self.save()
    
    def __str__(self):
        return self.first_name
    
class PropertyType(models.Model):
    property_type = models.CharField(max_length=255, null=True, blank=True)
    time_duration = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True, default=None, editable=False)

    def delete(self, hard=False, **kwargs):
        if hard:
            super(PropertyType, self).delete()
        else:
            self.deleted_at = now()
            self.save()
    
    def __str__(self):
        return self.property_type
    
class RoomType(models.Model):
    room_type = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True, default=None, editable=False)

    def delete(self, hard=False, **kwargs):
        if hard:
            super(RoomType, self).delete()
        else:
            self.deleted_at = now()
            self.save()
    
    def __str__(self):
        return self.room_type
    
class BedType(models.Model):
    bed_type = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True, default=None, editable=False)

    def delete(self, hard=False, **kwargs):
        if hard:
            super(BedType, self).delete()
        else:
            self.deleted_at = now()
            self.save()
    
    def __str__(self):
        return self.bed_type


class BathroomType(models.Model):
    bathroom_type = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True, default=None, editable=False)

    def delete(self, hard=False, **kwargs):
        if hard:
            super(BathroomType, self).delete()
        else:
            self.deleted_at = now()
            self.save()
    
    def __str__(self):
        return self.bathroom_type
    

class RoomFeature(models.Model):
    room_feature = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True, default=None, editable=False)

    def delete(self, hard=False, **kwargs):
        if hard:
            super(RoomFeature, self).delete()
        else:
            self.deleted_at = now()
            self.save()
    
    def __str__(self):
        return self.room_feature
    
class CommonAmenities(models.Model):
    common_ameninity = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True, default=None, editable=False)

    def delete(self, hard=False, **kwargs):
        if hard:
            super(CommonAmenities, self).delete()
        else:
            self.deleted_at = now()
            self.save()
    
    def __str__(self):
        return self.common_ameninity
    
class ExperienceSlot(models.Model):
    slot = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True, default=None, editable=False)

    def delete(self, hard=False, **kwargs):
        if hard:
            super(ExperienceSlot, self).delete()
        else:
            self.deleted_at = now()
            self.save()
    
    def __str__(self):
        return self.slot