from rest_framework import serializers 
from .models import Owner, PropertyType, RoomType, BedType, BathroomType, RoomFeature, CommonAmenities


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Owner
        fields = '__all__'

    is_verified = serializers.CharField(required=False)
    is_active = serializers.CharField(required=False)
    bidding_mode = serializers.CharField(required=False)


class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = Owner
        fields = ('phone_number',)


class OwnerProfileSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = Owner
        fields = ('first_name', 'last_name', 'email', 'profile_image', 'address', 'phone_number', 'bidding_mode', 'government_id')
        read_only_fields = ['government_id']


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