from rest_framework import serializers
from .models import Owner, PropertyType, RoomType, BedType, BathroomType, RoomFeature, BiddingSession, \
    CommonAmenities, Property, RoomInventory, UpdateInventoryPeriod, OTP, RoomImage, UpdateType, PropertyDeal, \
    Category, PropertyImage, PropertyCancellation, BookingHistory, OwnerBankingDetail, Ratings, BankingAddress, \
    Product, SubscriptionPlan, SubscriptionTransaction, GuestDetail, CancellationReason, SubCancellationReason
from customer.models import Customer
from dateutil.relativedelta import relativedelta


class DynamicFieldsModelSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)

        super().__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'category', 'bid_time_duration')


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Owner
        fields = '__all__'
    email = serializers.EmailField()
    government_id = serializers.CharField(required=False)
    profile_image = serializers.CharField(required=False)
    read_only_fields = ('is_verified', 'is_active', 'bidding_mode')

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        category_instance = instance.category
        if category_instance:
            ret['category'] = CategorySerializer(category_instance).data
        else:
            ret['category'] = None
        return ret


class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = Owner
        fields = '__all__'
        read_only_fields = ('hotel_name', 'email', 'profile_image', 'address', 'government_id', 'gst', 'is_verified', 'is_email_verified', 'is_active', 'bidding_mode', 'created_at', 'updated_at', 'deleted_at')

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        category_instance = instance.category
        if category_instance:
            ret['category'] = CategorySerializer(category_instance).data
        else:
            ret['category'] = None
        return ret


class OwnerProfileSerializer(DynamicFieldsModelSerializer):
    category = CategorySerializer()

    class Meta:
        model = Owner
        fields = ('id', 'hotel_name', 'email', 'profile_image', 'address', 'phone_number', 'category', 'bidding_mode', 'government_id', 'gst', 'is_verified', 'is_active', 'is_email_verified')
        read_only_fields = ('id', 'is_verified', 'is_active', 'is_email_verified')


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ('image',)


class PropertyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyType
        fields = ('id', 'property_type')


class RoomTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomType
        fields = ('id', 'room_type')


class BedTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BedType
        fields = ('id', 'bed_type')


class BathroomTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BathroomType
        fields = ('id', 'bathroom_type')


class RoomFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomFeature
        fields = ('id', 'room_feature')


class CommonAmenitiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommonAmenities
        fields = ('id', 'common_ameninity')


class CancellationSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyCancellation
        exclude = ['created_at', 'updated_at']


class UpdateTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UpdateType
        exclude = ['created_at', 'updated_at']


class PropertySerializer(serializers.ModelSerializer):
    images = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = Property
        exclude = ['owner']


class PropertyOutSerializer(DynamicFieldsModelSerializer):
    room_types = RoomTypeSerializer(many=True)
    property_type = PropertyTypeSerializer()
    address = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()
    cancellation_policy = serializers.SerializerMethodField()
    owner = OwnerProfileSerializer(fields=('hotel_name', 'email', 'phone_number'))

    def get_address(self, instance):
        owner = instance.owner
        return owner.address if owner and hasattr(owner, 'address') else None

    def get_images(self, obj):
        image_urls = [image.image for image in PropertyImage.objects.filter(property=obj) if image.property is not None]
        return image_urls

    def get_cancellation_policy(self, obj):
        cancellation_policies = [CancellationSerializer(policy).data for policy in PropertyCancellation.objects.filter(property=obj)]
        return cancellation_policies

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['location'] = {
            'type': 'Point',
            'coordinates': [instance.location.x, instance.location.y]
        }
        return representation

    class Meta:
        model = Property
        fields = ['id', 'owner', 'parent_hotel_group', 'hotel_nick_name', 'manager_name', 'hotel_phone_number',
                  'hotel_website', 'number_of_rooms', 'check_in_time', 'check_out_time', 'location',
                  'nearby_popular_landmark', 'property_type', 'room_types', 'pet_friendly', 'breakfast_included',
                  'is_cancellation', 'status', 'address', 'images', 'cancellation_policy', 'hotel_class',
                  'is_verified', 'created_at', 'updated_at']


class UpdatedPeriodSerializer(DynamicFieldsModelSerializer):
    dates = serializers.ListField(child=serializers.DateTimeField(), required=False)
    # removed_dates = serializers.ListField(child=serializers.DateTimeField(), required=False)

    class Meta:
        model = UpdateInventoryPeriod
        exclude = ['created_at', 'updated_at', 'room_inventory']


class RoomInventorySerializer(serializers.ModelSerializer):
    updated_period = UpdatedPeriodSerializer(required=False)
    images = serializers.ListField(child=serializers.CharField(), required=False)
    removed_images = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = RoomInventory
        exclude = ['property']


class UpdateInventoryPeriodSerializer(serializers.ModelSerializer):
    # type = serializers.CharField(source='type.type')

    class Meta:
        model = UpdateInventoryPeriod
        fields = ['date', 'default_price']


class RoomInventoryOutSerializer(DynamicFieldsModelSerializer):
    room_type = RoomTypeSerializer()
    bed_type = BedTypeSerializer(many=True)
    bathroom_type = BathroomTypeSerializer()
    room_features = RoomFeatureSerializer(many=True)
    common_amenities = CommonAmenitiesSerializer(many=True)
    images = serializers.SerializerMethodField()

    def get_images(self, obj):
        image_urls = [image.image for image in RoomImage.objects.filter(room=obj) if image.room is not None]
        return image_urls

    class Meta:
        model = RoomInventory
        fields = ('id', 'room_type', 'bed_type', 'bathroom_type', 'room_features', 'common_amenities', 'room_name',
                  'floor', 'room_view', 'area_sqft', 'num_of_rooms', 'adult_capacity', 'children_capacity', 'default_price',
                  'min_price', 'max_price', 'deal_price', 'is_verified', 'status', 'images')


class OTPVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ('otp',)


class BankingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankingAddress
        exclude = ['created_at', 'updated_at', 'owner_banking']


class HotelOwnerBankingSerializer(serializers.ModelSerializer):
    email = serializers.CharField(required=False)
    phone = serializers.CharField(required=False)
    contact_name = serializers.CharField()
    legal_business_name = serializers.CharField()
    business_type = serializers.CharField()
    type = serializers.CharField(required=False)
    account_id = serializers.CharField(required=False)
    status = serializers.BooleanField(required=False)
    addresses = BankingAddressSerializer(required=False, write_only=True)

    class Meta:
        model = OwnerBankingDetail
        fields = ['id', 'account_id', 'email', 'phone', 'contact_name', 'legal_business_name',
                  'business_type', 'type', 'status', 'category', 'subcategory', 'addresses']

    def create(self, validated_data):
        address_data = validated_data.pop('addresses', {})
        owner_banking_detail = OwnerBankingDetail.objects.create(**validated_data)
        BankingAddress.objects.create(owner_banking=owner_banking_detail, **address_data)
        return owner_banking_detail


class SettlementSerializer(serializers.Serializer):
    account_number = serializers.CharField()
    ifsc_code = serializers.CharField()
    beneficiary_name = serializers.CharField()


class PatchRequestSerializer(serializers.Serializer):
    settlements = SettlementSerializer()
    tnc_accepted = serializers.BooleanField()


class CustomerOutSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = Customer
        fields = ('first_name', 'last_name', 'phone_number')


class BookingHistorySerializer(DynamicFieldsModelSerializer):
    customer = CustomerOutSerializer()
    rooms = RoomInventoryOutSerializer(fields=('room_name', 'room_type'))
    property = serializers.SerializerMethodField()
    guests = serializers.SerializerMethodField()
    address = serializers.SerializerMethodField()

    def get_guests(self, instance):
        guests = GuestDetail.objects.filter(booking=instance).first()
        return guests.no_of_adults + guests.no_of_children if guests else None

    def get_property(self, instance):
        owner = instance.property.owner
        return owner.hotel_name

    def get_address(self, instance):
        owner = instance.property.owner
        return owner.address

    class Meta:
        model = BookingHistory
        exclude = ('updated_at',)


class TransactionSerializer(BookingHistorySerializer):
    class Meta:
        model = BookingHistory
        fields = [
            'id', 'customer', 'rooms', 'property', 'guests', 'address', 'num_of_rooms', 'order_id', 'transfer_id',
            'check_in_date', 'check_out_date', 'amount', 'currency', 'is_cancel', 'cancel_date', 'cancel_reason',
            'book_status', 'payment_id', 'is_confirmed', 'created_at', 'property_deal'
        ]


class AccountSerializer(HotelOwnerBankingSerializer):
    product_id = serializers.CharField(required=False)
    settlements_ifsc_code = serializers.CharField(required=False)
    settlements_beneficiary_name = serializers.CharField(required=False)
    settlements_account_number = serializers.CharField(required=False)

    class Meta(HotelOwnerBankingSerializer.Meta):
        fields = HotelOwnerBankingSerializer.Meta.fields + ['product_id', 'settlements_ifsc_code', 'settlements_beneficiary_name', 'settlements_account_number']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            address = BankingAddress.objects.get(owner_banking=instance)
            product = Product.objects.get(owner_banking=instance)
            data['postal_code'] = address.postal_code if address else None
            data['product_id'] = product.product_id
            data['settlements_ifsc_code'] = product.settlements_ifsc_code
            data['settlements_beneficiary_name'] = product.settlements_beneficiary_name
            data['settlements_account_number'] = product.settlements_account_number
        except Product.DoesNotExist:
            pass
        return data


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionTransaction
        fields = ['subscription_plan',]


class SubscriptionOutSerializer(serializers.ModelSerializer):
    subscription_plan = SubscriptionPlanSerializer()
    owner = OwnerProfileSerializer(fields=('hotel_name', 'email', 'phone_number'))
    start_date = serializers.DateTimeField(source='created_at', format='%Y-%m-%d')
    end_date = serializers.SerializerMethodField()

    def get_end_date(self, obj):
        end_date = obj.created_at + relativedelta(months=obj.subscription_plan.duration)
        return end_date.strftime('%Y-%m-%d')

    class Meta:
        model = SubscriptionTransaction
        fields = ['id', 'subscription_plan', 'owner', 'razorpay_subscription_id', 'payment_status', 'start_date', 'end_date']


class RatingsOutSerializer(serializers.ModelSerializer):
    customer = CustomerOutSerializer()

    class Meta:
        model = Ratings
        fields = '__all__'


class SubCancellationReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCancellationReason
        exclude = ['created_at', 'updated_at', 'main_reason']


class CancellationReasonSerializer(serializers.ModelSerializer):
    sub_reasons = serializers.SerializerMethodField()

    class Meta:
        model = CancellationReason
        fields = ['id', 'reason', 'sub_reasons']

    def get_sub_reasons(self, obj):
        sub_reasons_qs = SubCancellationReason.objects.filter(main_reason=obj).all()
        return SubCancellationReasonSerializer(sub_reasons_qs, many=True).data


class CancelBookingSerializer(serializers.ModelSerializer):
    cancel_reason = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = BookingHistory
        fields = ['cancel_reason']


class BookingRetrieveSerializer(BookingHistorySerializer):
    cancellation_policy = serializers.SerializerMethodField()
    num_of_adults = serializers.SerializerMethodField()
    num_of_children = serializers.SerializerMethodField()

    def get_cancellation_policy(self, obj):
        cancellation_policies = [CancellationSerializer(policy).data for policy in PropertyCancellation.objects.filter(property=obj.property)]
        return cancellation_policies

    def get_num_of_adults(self, instance):
        guests = GuestDetail.objects.filter(booking=instance).first()
        return guests.no_of_adults

    def get_num_of_children(self, instance):
        guests = GuestDetail.objects.filter(booking=instance).first()
        return guests.no_of_children


class BiddingSessionSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = BiddingSession
        fields = '__all__'


class PropertyDealSerializer(serializers.ModelSerializer):
    customer = CustomerOutSerializer(fields=('first_name', "last_name"))
    room_inventory = RoomInventoryOutSerializer(fields=('room_type', 'room_name', 'deal_price'))
    session = BiddingSessionSerializer(fields=('id', 'is_open', 'no_of_adults', 'no_of_children', 'num_of_rooms', 'check_in_date', 'check_out_date'))

    class Meta:
        model = PropertyDeal
        fields = ['id', 'customer', 'room_inventory', 'session', 'is_winning_bid', 'is_active', 'created_at', 'updated_at']
