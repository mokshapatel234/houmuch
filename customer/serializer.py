from rest_framework import serializers
from .models import Customer
from hotel.serializer import PropertyOutSerializer, DynamicFieldsModelSerializer
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
    price = serializers.SerializerMethodField()

    def get_price(self, obj):
        room_inventory_instance = RoomInventory.objects.filter(property=obj).order_by('default_price').first()
        return room_inventory_instance.default_price
