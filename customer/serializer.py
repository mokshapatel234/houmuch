from rest_framework import serializers
from .models import Customer
from hotel.serializer import PropertyOutSerializer, DynamicFieldsModelSerializer, RoomInventoryOutSerializer
from hotel.models import RoomInventory, Property


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


class PopertyListOutSerializer(PropertyOutSerializer):
    # room_inventory = serializers.SerializerMethodField()
    room_inventory = serializers.ListField()
    # def get_room_inventory(self, obj):
    #     num_of_rooms = self.context.get('num_of_rooms', None)
    #     min_price = self.context.get('min_price', None)
    #     max_price = self.context.get('max_price', None)
    #     is_preferred_property_type = self.context.get('is_preferred_property_type', None)
    #     room_inventory_instances = RoomInventory.objects.filter(property=obj).order_by('default_price')
    #     if num_of_rooms is not None and num_of_rooms > 0 and is_preferred_property_type is None:
    #         room_inventory_instances = list(room_inventory_instances[:num_of_rooms])
    #     if min_price is not None and max_price is not None:
    #         room_inventory_instances = [
    #             room_instance for room_instance in room_inventory_instances 
    #             if (min_price is None or room_instance.default_price >= float(min_price)) and 
    #             (max_price is None or room_instance.default_price <= float(max_price))
    #         ]
    #     if is_preferred_property_type:
    #         room_inventory_instances = list(room_inventory_instances)
    #     else:
    #         room_inventory_instances = room_inventory_instances[:1]
    #     return [RoomInventoryOutSerializer(room_instance).data for room_instance in room_inventory_instances]

    class Meta:
        model = Property
        fields = ['id', 'parent_hotel_group', 'hotel_nick_name', 'manager_name', 'hotel_phone_number',
                  'hotel_website', 'number_of_rooms', 'check_in_time', 'check_out_time', 'location',
                  'nearby_popular_landmark', 'property_type', 'room_types', 'cancellation_days', 'cancellation_policy',
                  'pet_friendly', 'breakfast_included', 'is_cancellation', 'status', 'is_online', 'created_at',
                  'updated_at', 'address', 'images', 'room_inventory']
