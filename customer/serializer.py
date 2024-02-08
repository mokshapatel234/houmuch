from rest_framework import serializers
from .models import Customer
from hotel.serializer import PropertyOutSerializer, DynamicFieldsModelSerializer, RoomInventoryOutSerializer
from hotel.models import RoomInventory


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
    room_inventory = serializers.SerializerMethodField()
    capacity_issue_message = serializers.SerializerMethodField()


    def get_room_inventory(self, obj):
        num_of_rooms = self.context.get('num_of_rooms', None)
        room_inventory_instances = RoomInventory.objects.filter(property=obj, is_verified=True).order_by('default_price')
        
        if num_of_rooms is not None and num_of_rooms > 0:
            room_inventory_instances = list(room_inventory_instances[:num_of_rooms])
        else:
            room_inventory_instances = room_inventory_instances[:1]
        return [RoomInventoryOutSerializer(room_instance).data for room_instance in room_inventory_instances]

    def get_capacity_issue_message(self, obj):
        meets_capacity = self.context.get('meets_capacity', True)
        if not meets_capacity:
            return 'This property does not meet the required capacity for your search criteria.'
        return ''  # or None, depending on how you want to handle properties that meet the criteria
