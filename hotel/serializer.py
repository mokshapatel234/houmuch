from rest_framework import serializers
from .models import Owner, PropertyType, RoomType, BedType, BathroomType, RoomFeature, \
    CommonAmenities, Property, RoomInventory, UpdateInventoryPeriod, OTP, Image
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


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Owner
        fields = '__all__'
    email = serializers.EmailField()
    government_id = serializers.CharField(required=False)
    profile_image = serializers.CharField(required=False)
    read_only_fields = ('is_verified', 'is_active', 'bidding_mode')


class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = Owner
        fields = '__all__'
        read_only_fields = ('hotel_name', 'email', 'profile_image', 'address', 'government_id', 'gst', 'is_verified', 'is_email_verified', 'is_active', 'bidding_mode', 'created_at', 'updated_at', 'deleted_at')


class OwnerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Owner
        fields = ('hotel_name', 'email', 'profile_image', 'address', 'phone_number', 'bidding_mode', 'government_id', 'gst', 'is_verified', 'is_active', 'is_email_verified')
        read_only_fields = ('is_verified', 'is_active', 'is_email_verified')


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
    class Meta:
        model = Property
        exclude = ['owner']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['location'] = {
            'type': 'Point',
            'coordinates': [instance.location.x, instance.location.y]
        }
        return representation


class PropertyOutSerializer(PropertySerializer):
    room_types = RoomTypeSerializer(many=True)
    property_type = PropertyTypeSerializer()
    address = serializers.SerializerMethodField()

    def get_address(self, instance):
        owner = instance.owner
        return owner.address if owner and hasattr(owner, 'address') else None


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


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ('image', 'created_at', 'updated_at')


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
        image_urls = [image.image for image in Image.objects.filter(room_image=obj) if image.room_image is not None]
        return image_urls

    class Meta:
        model = RoomInventory
        fields = ('id', 'room_type', 'bed_type', 'bathroom_type', 'room_features', 'common_amenities', 'room_name',
                  'floor', 'room_view', 'area_sqft', 'adult_capacity', 'children_capacity', 'default_price',
                  'min_price', 'max_price', 'status', 'images', 'updated_period', 'created_at', 'updated_at', 'deleted_at')


class OTPVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ('otp',)
