from rest_framework import serializers
from .models import Owner, PropertyType, RoomType, BedType, BathroomType, RoomFeature, CommonAmenities, Property, OTP


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Owner
        fields = '__all__'
    email = serializers.EmailField(required=False)
    address = serializers.CharField(required=False)
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


class RoomTypeSerilizer(serializers.ModelSerializer):
    class Meta:
        model = RoomType
        fields = ('id', 'room_type')


class PropertyTypeSerilizer(serializers.ModelSerializer):
    class Meta:
        model = PropertyType
        fields = ('id', 'property_type')


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
    room_types = RoomTypeSerilizer(many=True)
    property_type = PropertyTypeSerilizer()


class PropertyTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyType
        fields = '__all__'


class RoomTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomType
        fields = '__all__'


class BedTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BedType
        fields = '__all__'


class BathroomTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BathroomType
        fields = '__all__'


class RoomFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomFeature
        fields = '__all__'


class CommonAmenitiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommonAmenities
        fields = '__all__'


class OTPVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ('otp',)
