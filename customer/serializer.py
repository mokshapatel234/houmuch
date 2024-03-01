from rest_framework import serializers
from .models import Customer
from hotel.serializer import PropertyOutSerializer
from hotel.models import Property, RoomInventory, BookingHistory, GuestDetail
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
    available_rooms = serializers.IntegerField()

    class Meta:
        model = RoomInventory
        fields = ['id', 'default_price', 'deal_price', 'available_rooms', 'adult_capacity',
                  'children_capacity', 'room_type', 'is_verified', 'status', 'updated_period']


class RoomInventoryListSerializer(RoomInventoryOutSerializer):
    available_rooms = serializers.IntegerField()

    class Meta(RoomInventoryOutSerializer.Meta):
        fields = RoomInventoryOutSerializer.Meta.fields + ('available_rooms',)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        updated_availability = self.context.get('adjusted_availability', {})
        if instance.id in updated_availability:
            ret['available_rooms'] = updated_availability[instance.id]
        return ret


class PopertyListOutSerializer(PropertyOutSerializer):
    room_inventory = serializers.DictField()

    class Meta:
        model = Property
        fields = ['id', 'parent_hotel_group', 'hotel_nick_name', 'manager_name', 'hotel_phone_number',
                  'hotel_website', 'number_of_rooms', 'check_in_time', 'check_out_time', 'location',
                  'nearby_popular_landmark', 'property_type', 'room_types', 'pet_friendly', 'breakfast_included',
                  'is_cancellation', 'status', 'is_online', 'address', 'images', 'is_verified', 'cancellation_policy', 'room_inventory']


class OrderSummarySerializer(RoomInventoryOutSerializer):
    property_name = serializers.SerializerMethodField()

    def get_property_name(self, obj):
        return obj.property.owner.hotel_name

    class Meta:
        model = RoomInventory
        fields = ['id', 'default_price', 'property_name', 'children_capacity', 'room_type', 'is_verified', 'status', 'updated_period']


class BookingHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingHistory
        exclude = ['property', 'order_id', 'customer', 'book_status', 'rooms', 'currency', 'is_cancel', 'cancel_date', 'cancel_reason', 'property_deal']


class GuestDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuestDetail
        fields = ['booking_id', 'no_of_adults', 'no_of_children', 'age_of_children']


class CombinedSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    property_id = serializers.IntegerField()
    room_id = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    check_in_date = serializers.DateTimeField()
    check_out_date = serializers.DateTimeField()
    num_of_rooms = serializers.IntegerField()  # Add this field
    no_of_adults = serializers.IntegerField()
    no_of_children = serializers.IntegerField()
    age_of_children = serializers.CharField(max_length=100)

    def validate(self, data):
        # Add custom validation logic here if needed
        return data

    def create(self, validated_data):
        try:
            property_instance = Property.objects.get(id=validated_data['property_id'])
            room_instance = RoomInventory.objects.get(id=validated_data['room_id'])

            # Create BookingHistory instance
            booking_instance = BookingHistory.objects.create(property=property_instance, rooms=room_instance,
                                                             amount=validated_data['amount'],
                                                             check_in_date=validated_data['check_in_date'],
                                                             check_out_date=validated_data['check_out_date'],
                                                             num_of_rooms=validated_data['num_of_rooms'],
                                                             customer_id=validated_data['customer_id'],
                                                             currency=validated_data['currency'],
                                                             order_id=validated_data['order_id'])  # Set num_of_rooms
            booking_instance.book_status = True  # or any other value
            booking_instance.save()
            # Create GuestDetail instance
            guest_instance = GuestDetail.objects.create(booking_id=booking_instance,
                                                        no_of_adults=validated_data['no_of_adults'],
                                                        no_of_children=validated_data['no_of_children'],
                                                        age_of_children=validated_data['age_of_children'])

            return {'booking_instance': booking_instance, 'guest_instance': guest_instance}
        except Exception as e:
            # Handle exceptions here
            raise serializers.ValidationError(str(e))
