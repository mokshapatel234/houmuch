from rest_framework import serializers
from .models import Owner, PropertyType, RoomType, BedType, BathroomType, RoomFeature, \
    CommonAmenities, Property, RoomInventory, UpdateInventoryPeriod, OTP, RoomImage, Category, PropertyImage
from django.utils import timezone


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


class OwnerProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Owner
        fields = ('id', 'hotel_name', 'email', 'profile_image', 'address', 'phone_number', 'category', 'bidding_mode', 'government_id', 'gst', 'is_verified', 'is_active', 'is_email_verified')
        read_only_fields = ('id', 'is_verified', 'is_active', 'is_email_verified')

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        category_instance = instance.category
        if category_instance:
            ret['category'] = CategorySerializer(category_instance).data
        else:
            ret['category'] = None
        return ret


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

    def get_address(self, instance):
        owner = instance.owner
        return owner.address if owner and hasattr(owner, 'address') else None

    def get_images(self, obj):
        image_urls = [image.image for image in PropertyImage.objects.filter(property=obj) if image.property is not None]
        return image_urls

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['location'] = {
            'type': 'Point',
            'coordinates': [instance.location.x, instance.location.y]
        }
        return representation

    class Meta:
        model = Property
        fields = ['id', 'parent_hotel_group', 'hotel_nick_name', 'manager_name', 'hotel_phone_number', 'hotel_website', 'number_of_rooms', 'check_in_time', 'check_out_time', 'location', 'nearby_popular_landmark', 'property_type', 'room_types', 'cancellation_days', 'cancellation_policy', 'pet_friendly', 'breakfast_included', 'is_cancellation', 'status', 'is_online', 'created_at', 'updated_at', 'address', 'images']


class UpdatedPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = UpdateInventoryPeriod
        exclude = ['created_at', 'updated_at', 'deleted_at', 'room_inventory']


class UpdatedPeriodOutSerializer(UpdatedPeriodSerializer):
    common_amenities = CommonAmenitiesSerializer(many=True)


class RoomInventorySerializer(serializers.ModelSerializer):
    updated_period = UpdatedPeriodSerializer(required=False)
    images = serializers.ListField(child=serializers.CharField(), required=False)
    removed_images = serializers.ListField(child=serializers.CharField(), required=False)

    class Meta:
        model = RoomInventory
        exclude = ['property']


class RoomInventoryOutSerializer(DynamicFieldsModelSerializer):
    room_type = RoomTypeSerializer()
    bed_type = BedTypeSerializer(many=True)
    bathroom_type = BathroomTypeSerializer()
    room_features = RoomFeatureSerializer(many=True)
    common_amenities = CommonAmenitiesSerializer(many=True)
    updated_period = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    def get_updated_period(self, obj):
        duration_mapping = {
            'today': timezone.timedelta(days=1),
            'for a week': timezone.timedelta(days=7),
            'for a month': timezone.timedelta(days=30),
        }

        for update_period in UpdateInventoryPeriod.objects.filter(room_inventory=obj):
            if (
                update_period.update_duration.lower() in duration_mapping
                and timezone.now() - update_period.created_at <= duration_mapping[update_period.update_duration.lower()]
            ):
                return UpdatedPeriodOutSerializer(update_period).data

        return None

    def get_images(self, obj):
        image_urls = [image.image for image in RoomImage.objects.filter(room=obj) if image.room is not None]
        return image_urls

    class Meta:
        model = RoomInventory
        fields = ('id', 'room_type', 'bed_type', 'bathroom_type', 'room_features', 'common_amenities', 'room_name',
                  'floor', 'room_view', 'area_sqft', 'adult_capacity', 'num_of_rooms','children_capacity', 'default_price',
                  'min_price', 'max_price', 'deal_price', 'is_verified', 'status', 'images', 'updated_period', 'created_at', 'updated_at', 'deleted_at')


class OTPVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ('otp',)
