from rest_framework import serializers 
from .models import Owner, PropertyType, RoomType, BedType, BathroomType, RoomFeature, CommonAmenities


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Owner
        fields = '__all__'

    read_only_fields = ('is_verified', 'is_active', 'bidding_mode')


class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model=Owner
        fields = '__all__'
        read_only_fields = ('first_name', 'last_name', 'email', 'profile_image', 'address', 'government_id', 'is_verified', 'is_active', 'bidding_mode', 'created_at', 'updated_at', 'deleted_at')


class OwnerProfileSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = Owner
        fields = ('first_name', 'last_name', 'email', 'profile_image', 'address', 'phone_number', 'bidding_mode', 'government_id', 'is_verified', 'is_active',)
        read_only_fields = ('is_verified', 'is_active')


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