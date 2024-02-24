from rest_framework import serializers
from .models import Customer
from hotel.serializer import PropertyOutSerializer
from hotel.models import Property, RoomInventory, BookingHistory
from hotel.serializer import RoomInventoryOutSerializer


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'

    email = serializers.EmailField(required=False)
    address = serializers.CharField(required=False)
    government_id = serializers.CharField(required=False)
    profile_image = serializers.CharField(required=False)


class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
        read_only_fields = ('first_name', 'last_name', 'email', 'profile_image', 'address', 'government_id', 'created_at', 'updated_at', 'deleted_at')


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ('first_name', 'last_name', 'phone_number', 'email', 'address', 'government_id', 'profile_image')


class RoomInventorySerializer(RoomInventoryOutSerializer):

    class Meta:
        model = RoomInventory
        fields = ['id', 'default_price', 'adult_capacity', 'children_capacity', 'room_type', 'is_verified', 'status', 'updated_period']


class PopertyListOutSerializer(PropertyOutSerializer):
    room_inventory = serializers.ListField()

    class Meta:
        model = Property
        fields = ['id', 'parent_hotel_group', 'hotel_nick_name', 'manager_name', 'hotel_phone_number',
                  'hotel_website', 'number_of_rooms', 'check_in_time', 'check_out_time', 'location',
                  'nearby_popular_landmark', 'property_type', 'room_types', 'cancellation_days', 'cancellation_policy',
                  'pet_friendly', 'breakfast_included', 'is_cancellation', 'status', 'is_online', 'address', 'images', 'room_inventory']


class OrderSummarySerializer(RoomInventoryOutSerializer):
    property_name = serializers.SerializerMethodField()

    def get_property_name(self, obj):
        return obj.property.owner.hotel_name

    class Meta:
        model = RoomInventory
        fields = ['id', 'default_price', 'property_name', 'children_capacity', 'room_type', 'is_verified', 'status', 'updated_period']


class BookingHistorySerializer(serializers.ModelSerializer):
    room_id = serializers.IntegerField() 
    property_id = serializers.IntegerField() 
    amount = serializers.FloatField()
    class Meta:
        model = BookingHistory
        fields = ['property_id', 'num_of_rooms', 'room_id', 'amount', 'check_in_date', 'check_out_date']