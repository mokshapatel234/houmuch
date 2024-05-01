from django.db import models
from hotel_app_backend.validator import PhoneNumberRegex
from django.contrib.gis.db import models as geo_models
from django.contrib.gis.geos import Point
from customer.models import Customer
from django.core.validators import RegexValidator


class Category(models.Model):
    category = models.CharField(max_length=255, null=True, blank=True)
    bid_time_duration = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

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
    bidding_mode = models.BooleanField(default=False)
    fcm_token = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def is_authenticated(self):
        return True

    def is_anonymous(self):
        return False

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

    def __str__(self):
        return self.property_type


class RoomType(models.Model):
    room_type = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.room_type


class BedType(models.Model):
    bed_type = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.bed_type


class BathroomType(models.Model):
    bathroom_type = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.bathroom_type


class RoomFeature(models.Model):
    room_feature = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.room_feature


class CommonAmenities(models.Model):
    common_ameninity = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.common_ameninity

    class Meta:
        verbose_name_plural = "Common amenities"


class ExperienceSlot(models.Model):
    slot = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

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
    commission_percent = models.FloatField('Commission', default=10.0)
    hotel_class = models.IntegerField(default=0)
    pet_friendly = models.BooleanField('Pet Friendly', default=False)
    breakfast_included = models.BooleanField('Breakfast Included', default=False)
    is_cancellation = models.BooleanField('Is Cancellation Allowed', default=False)
    status = models.BooleanField('Status', default=False)
    is_verified = models.BooleanField('Is Verified', default=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.hotel_website

    class Meta:
        verbose_name_plural = "Properties"


class PropertyCancellation(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, blank=True, null=True)
    cancellation_days = models.IntegerField('Cancellation Days')
    cancellation_percents = models.IntegerField('Cancellation Percents')
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.property.hotel_nick_name


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
    num_of_rooms = models.IntegerField(("Num Of Rooms"), default=0)
    adult_capacity = models.IntegerField(("Adult Capacity"))
    children_capacity = models.IntegerField(("Children Capacity"))
    default_price = models.IntegerField(('Default Price'))
    deal_price = models.IntegerField(('Deal Price'), default=None, null=True)
    min_price = models.IntegerField(('Min Price'))
    max_price = models.IntegerField(('Max Price'))
    is_verified = models.BooleanField('Is Verified', default=False)
    status = models.BooleanField('Status', default=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.room_name

    class Meta:
        verbose_name_plural = "Room inventories"


class UpdateType(models.Model):
    type = models.CharField(("Type"), max_length=255)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.type


class UpdateRequest(models.Model):
    request = models.TextField()
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.request


class UpdateInventoryPeriod(models.Model):
    room_inventory = models.ForeignKey(RoomInventory, on_delete=models.CASCADE, related_name='update_room', null=True, blank=True)
    type = models.ForeignKey(UpdateType, on_delete=models.CASCADE, related_name="update_type", null=True)
    default_price = models.IntegerField(('Default Price'), default=0)
    deal_price = models.IntegerField(('Deal Price'), default=0, null=True)
    min_price = models.IntegerField(('Min Price'), default=0)
    max_price = models.IntegerField(('Max Price'), default=0)
    num_of_rooms = models.IntegerField(("Num Of Rooms"), default=0)
    date = models.DateTimeField(blank=True, null=True)
    request = models.ForeignKey(UpdateRequest, on_delete=models.CASCADE, related_name="update_request", null=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.type.type


class RoomImage(models.Model):
    room = models.ForeignKey(RoomInventory, on_delete=models.CASCADE, blank=True, null=True)
    image = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.image


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, blank=True, null=True)
    image = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.image


class OTP(models.Model):
    user = models.ForeignKey(Owner, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.user.hotel_name


class BiddingSession(models.Model):
    is_open = models.BooleanField(default=False)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_bid_id', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.created_at


class PropertyDeal(models.Model):
    session = models.ForeignKey(BiddingSession, on_delete=models.CASCADE, related_name='session_id')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_id')
    roominventory = models.ForeignKey(RoomInventory, on_delete=models.CASCADE, related_name='room_id', blank=True, null=True)
    is_winning_bid = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.session.created_at


class BookingHistory(models.Model):
    booking_id = models.CharField(max_length=255, unique=True, editable=False, null=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_book')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_book')
    property_deal = models.ForeignKey(PropertyDeal, on_delete=models.CASCADE, related_name='property_deal', null=True)
    num_of_rooms = models.IntegerField(verbose_name='number_of_book_rooms')
    rooms = models.ForeignKey(RoomInventory, on_delete=models.CASCADE, related_name='room_book', null=True)
    order_id = models.CharField(max_length=20)
    transfer_id = models.CharField(max_length=20, null=True)
    check_in_date = models.DateTimeField()
    check_out_date = models.DateTimeField()
    amount = models.FloatField()
    currency = models.CharField(max_length=3)
    is_cancel = models.BooleanField(default=False)
    cancel_by_owner = models.BooleanField(default=False)
    cancel_date = models.DateTimeField(null=True)
    cancel_reason = models.TextField(null=True, blank=True)
    book_status = models.BooleanField(default=False)
    payment_id = models.CharField(max_length=20, null=True)
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.property.hotel_nick_name


class GuestDetail(models.Model):
    booking = models.ForeignKey(BookingHistory, on_delete=models.CASCADE, related_name='booking_history')
    no_of_adults = models.IntegerField()
    no_of_children = models.IntegerField()
    age_of_children = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.no_of_adults + self.no_of_children)


class OwnerBankingDetail(models.Model):
    hotel_owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name='banking_details')
    email = models.EmailField(unique=True)
    phone = models.CharField(validators=[RegexValidator(regex=r"^\+?1?\d{10}$")], max_length=10, unique=True)
    contact_name = models.CharField(max_length=16)
    type = models.CharField(max_length=16)
    account_id = models.CharField(max_length=20)
    legal_business_name = models.CharField(max_length=16)
    business_type = models.CharField(max_length=50)
    category = models.CharField(max_length=255, null=True)
    subcategory = models.CharField(max_length=255, null=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(blank=True, null=True, default=None)

    def __str__(self):
        return self.contact_name


class Product(models.Model):
    product_id = models.CharField(max_length=30)
    owner_banking = models.ForeignKey(OwnerBankingDetail, on_delete=models.CASCADE, related_name='banking_id')
    settlements_account_number = models.CharField(max_length=30)
    settlements_ifsc_code = models.CharField(max_length=30)
    settlements_beneficiary_name = models.CharField(max_length=30)
    tnc_accepted = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.product_id


class BankingAddress(models.Model):
    owner_banking = models.ForeignKey(OwnerBankingDetail, on_delete=models.CASCADE, related_name='banking_address')
    street1 = models.CharField(max_length=255)
    street2 = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=30)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    def __str__(self):
        return self.postal_code


class SubscriptionPlan(models.Model):
    Plans = (
        (3, '3 months'),
        (6, '6 months'),
        (12, '12 months'),
    )
    name = models.CharField(('Plan'), max_length=30, null=False)
    price = models.IntegerField(('Price'), null=False)
    duration = models.IntegerField(('Plan Duration'), choices=Plans)
    description = models.TextField(('Description'), max_length=255, null=False)
    razorpay_plan_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class SubscriptionTransaction(models.Model):
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='subscription_plan')
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name='owner_subscription')
    razorpay_subscription_id = models.CharField(max_length=255, blank=True, null=True)
    payment_status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subscription_plan.name


class Ratings(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_ratings')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_ratings')
    ratings = models.IntegerField()
    review = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.ratings)


class CancellationReason(models.Model):
    reason = models.CharField(('Reason'), max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.reason


class SubCancellationReason(models.Model):
    main_reason = models.ForeignKey(CancellationReason, on_delete=models.CASCADE, related_name='main_cancel_reason')
    sub_reason = models.CharField(('Sub Reason'), max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.sub_reason


class BiddingAmount(models.Model):
    property_deal = models.ForeignKey(PropertyDeal, on_delete=models.CASCADE, related_name='property_deal_id')
    amount = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return self.amount
