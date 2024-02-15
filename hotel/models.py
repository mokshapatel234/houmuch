from django.db import models
from hotel_app_backend.validator import PhoneNumberRegex
from django.utils.timezone import now
from django.contrib.gis.db import models as geo_models
from django.contrib.gis.geos import Point
from customer.models import Customer

class ParanoidModelManager(models.Manager):
    def get_queryset(self):
        return super(ParanoidModelManager, self).get_queryset().filter(deleted_at__isnull=True)


class Category(models.Model):
    category = models.CharField(max_length=255, null=True, blank=True)
    bid_time_duration = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True, default=None, editable=False)
    objects = ParanoidModelManager()

    def delete(self, hard=False, **kwargs):
        if hard:
            super(PropertyType, self).delete()
        else:
            self.deleted_at = now()
            self.save()

    def __str__(self):
        return self.category

    class Meta:
        verbose_name_plural = "Categories"


class Owner(models.Model):
    hotel_name = models.CharField(('Hotel Name'), max_length=255, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="owner_category", null=True, blank=True)
    email = models.EmailField(max_length=100, null=True)
    phone_number = models.CharField(validators=[PhoneNumberRegex], max_length=17, blank=True)
    profile_image = models.CharField(max_length=255, null=True, blank=True)
    address = models.TextField(verbose_name='address', blank=True, null=True)
    government_id = models.TextField(verbose_name='gov_id', blank=True, null=True)
    gst = models.CharField(max_length=20, default=None, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    welcome_mail_sent = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    fcm_token = models.CharField(max_length=255, null=True, blank=True)
    bidding_mode = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True, default=None, editable=False)
    objects = ParanoidModelManager()

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
        return self.hotel_name


# class FCMToken(models.Model):
#     user_id = models.IntegerField()
#     fcm_token = models.CharField(max_length=255, null=True, blank=True)
#     is_owner = models.BooleanField(default=False)
#     created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
#     updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
#     deleted_at = models.DateTimeField(blank=True, null=True, default=None, editable=False)

#     def delete(self, hard=False, **kwargs):
#         if hard:
#             super(FCMToken, self).delete()
#         else:
#             self.deleted_at = now()
#             self.save()

#     def __str__(self):
#         return self.first_name


class PropertyType(models.Model):
    property_type = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True, default=None, editable=False)
    objects = ParanoidModelManager()

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
    objects = ParanoidModelManager()

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
    objects = ParanoidModelManager()

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
    objects = ParanoidModelManager()

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
    objects = ParanoidModelManager()

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
    objects = ParanoidModelManager()

    def delete(self, hard=False, **kwargs):
        if hard:
            super(CommonAmenities, self).delete()
        else:
            self.deleted_at = now()
            self.save()

    def __str__(self):
        return self.common_ameninity

    class Meta:
        verbose_name_plural = "Common amenities"


class ExperienceSlot(models.Model):
    slot = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True, default=None, editable=False)
    objects = ParanoidModelManager()

    def delete(self, hard=False, **kwargs):
        if hard:
            super(ExperienceSlot, self).delete()
        else:
            self.deleted_at = now()
            self.save()

    def __str__(self):
        return self.slot


class Property(models.Model):
    parent_hotel_group = models.CharField(('Parent Hotel Group'), max_length=255, null=True, blank=True)
    hotel_nick_name = models.CharField(('Hotel Nick Name'), max_length=255)
    manager_name = models.CharField(('Manager Name'), max_length=255)
    hotel_phone_number = models.CharField(max_length=20, blank=True)
    hotel_website = models.CharField(('Hotel website'), max_length=255, null=True, blank=True)
    number_of_rooms = models.IntegerField(verbose_name='number_of_rooms')
    check_in_time = models.CharField('Check-in time', null=True, blank=True)
    check_out_time = models.CharField('Check-out time', null=True, blank=True)
    location = geo_models.PointField(('Location'), geography=True, default=Point(0.0, 0.0))
    nearby_popular_landmark = models.CharField('Nearby Popular Landmark', max_length=255)
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name='owner_property')
    property_type = models.ForeignKey(PropertyType, on_delete=models.CASCADE, related_name='owner_property_type')
    room_types = models.ManyToManyField(RoomType, related_name='owner_room_type')
    cancellation_days = models.IntegerField('Cancellation Days', default=False)
    cancellation_policy = models.TextField('Cancellation Policy')
    pet_friendly = models.BooleanField('Pet Friendly', default=False)
    breakfast_included = models.BooleanField('Breakfast Included', default=False)
    is_cancellation = models.BooleanField('Is Cancellation Allowed', default=False)
    status = models.BooleanField('Status', default=False)
    is_online = models.BooleanField('Is Online', default=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True, default=None, editable=False)
    objects = ParanoidModelManager()

    def delete(self, hard=False, **kwargs):
        if hard:
            super(Property, self).delete()
        else:
            self.deleted_at = now()
            self.save()

    def __str__(self):
        return self.hotel_website

    class Meta:
        verbose_name_plural = "Properties"


class RoomInventory(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_room')
    room_name = models.CharField(('Room Name'), max_length=255)
    floor = models.IntegerField(('Floor'))
    room_view = models.CharField(('Room View'), max_length=255)
    area_sqft = models.FloatField(('Area sqft'))
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='property_room_type')
    bed_type = models.ManyToManyField(BedType, related_name='property_bed_type')
    bathroom_type = models.ForeignKey(BathroomType, on_delete=models.CASCADE, related_name='property_bathroom_type')
    room_features = models.ManyToManyField(RoomFeature, related_name='property_room_features')
    common_amenities = models.ManyToManyField(CommonAmenities, related_name='property_common_amenities')
    adult_capacity = models.IntegerField(("Adult Capacity"))
    children_capacity = models.IntegerField(("Children Capacity"))
    default_price = models.IntegerField(('Default Price'))
    min_price = models.IntegerField(('Min Price'))
    max_price = models.IntegerField(('Max Price'))
    is_verified = models.BooleanField(default=False)
    status = models.BooleanField('Status', default=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True, default=None, editable=False)
    objects = ParanoidModelManager()

    def delete(self, hard=False, **kwargs):
        if hard:
            super(RoomInventory, self).delete()
        else:
            self.deleted_at = now()
            self.save()

    def __str__(self):
        return self.room_name

    class Meta:
        verbose_name_plural = "Room inventories"


class UpdateInventoryPeriod(models.Model):
    update_duration = models.CharField(('Update Duration'), max_length=255)
    room_inventory = models.ForeignKey(RoomInventory, on_delete=models.CASCADE, related_name='update_room', null=True, blank=True)
    common_amenities = models.ManyToManyField(CommonAmenities, related_name='updated_common_amenities')
    default_price = models.IntegerField(('Default Price'))
    min_price = models.IntegerField(('Min Price'))
    max_price = models.IntegerField(('Max Price'))
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True, default=None, editable=False)
    objects = ParanoidModelManager()

    def delete(self, hard=False, **kwargs):
        if hard:
            super(UpdateInventoryPeriod, self).delete()
        else:
            self.deleted_at = now()
            self.save()

    def __str__(self):
        return self.update_duration


class RoomImage(models.Model):
    room = models.ForeignKey(RoomInventory, on_delete=models.CASCADE, blank=True, null=True)
    image = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True, default=None, editable=False)
    objects = ParanoidModelManager()

    def delete(self, hard=False, **kwargs):
        if hard:
            super(RoomImage, self).delete()
        else:
            self.deleted_at = now()
            self.save()

    def __str__(self):
        return self.image


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, blank=True, null=True)
    image = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True, default=None, editable=False)
    objects = ParanoidModelManager()

    def delete(self, hard=False, **kwargs):
        if hard:
            super(PropertyImage, self).delete()
        else:
            self.deleted_at = now()
            self.save()

    def __str__(self):
        return self.image


class OTP(models.Model):
    user = models.ForeignKey(Owner, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True, default=None, editable=False)
    objects = ParanoidModelManager()

    def delete(self, hard=False, **kwargs):
        if hard:
            super(OTP, self).delete()
        else:
            self.deleted_at = now()
            self.save()

    def __str__(self):
        return self.user

class BiddingSession(models.Model):
    is_open = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True, default=None, editable=False)
    objects = ParanoidModelManager()

    def delete(self, hard=False, **kwargs):
        if hard:
            super(BiddingSession, self).delete()
        else:
            self.deleted_at = now()
            self.save()

    def __str__(self):
        return self.is_open


class PropertyDeal(models.Model):
    session = models.ForeignKey(BiddingSession, on_delete=models.CASCADE, related_name='session_id')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_id')
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_id')
    is_winning_bid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True, default=None, editable=False)
    objects = ParanoidModelManager()

    def delete(self, hard=False, **kwargs):
        if hard:
            super(PropertyDeal, self).delete()
        else:
            self.deleted_at = now()
            self.save()

    def __str__(self):
        return self.session