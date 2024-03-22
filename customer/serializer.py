from rest_framework import serializers
from .models import Customer
from hotel.serializer import PropertyOutSerializer
from hotel.models import Property, RoomInventory, BookingHistory, GuestDetail, Ratings
from hotel.serializer import RoomInventoryOutSerializer, RoomTypeSerializer
from django.db.models import Avg


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
        read_only_fields = ['first_name', 'last_name', 'email', 'profile_image', 'address', 'government_id', 'created_at', 'updated_at', 'deleted_at']


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'phone_number', 'email', 'address', 'government_id', 'profile_image']


class RoomInventorySerializer(serializers.ModelSerializer):
    available_rooms = serializers.IntegerField()
    # updated_period = serializers.SerializerMethodField()
    # is_updated_period = serializers.SerializerMethodField()

    # def get_updated_period(self, obj):
    #     start_date = self.context['start_date']
    #     end_date = self.context['end_date']
    #     updated_period = UpdateInventoryPeriod.objects.filter(
    #         room_inventory=obj,
    #         start_date__date__lte=end_date,
    #     ).filter(
    #         Q(end_date__date__gte=start_date) | Q(end_date__isnull=True)
    #     ).first()

    #     if updated_period:
    #         return UpdatedPeriodSerializer(updated_period).data
    #     return None

    # def get_is_updated_period(self, obj):
    #     updated_period = self.get_updated_period(obj)
    #     return updated_period is not None

    class Meta:
        model = RoomInventory
        fields = ['id', 'default_price', 'deal_price', 'available_rooms', 'adult_capacity',
                  'children_capacity', 'room_type', 'is_verified', 'status']


class RoomInventoryListSerializer(RoomInventoryOutSerializer):
    available_rooms = serializers.IntegerField()

    class Meta(RoomInventoryOutSerializer.Meta):
        fields = RoomInventoryOutSerializer.Meta.fields + ('available_rooms',)

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        updated_availability = self.context.get('adjusted_availability', {})
        if instance.id in updated_availability:
            ret['available_rooms'] = updated_availability[instance.id]['available_rooms']
            ret['default_price'] = updated_availability[instance.id]['effective_price']
        return ret


class PopertyListOutSerializer(PropertyOutSerializer):
    room_inventory = serializers.DictField()
    average_ratings = serializers.SerializerMethodField()

    def get_average_ratings(self, obj):
        average = Ratings.objects.filter(property=obj).aggregate(average_rating=Avg('ratings'))
        return round(average['average_rating'], 2) if average['average_rating'] else 0

    class Meta:
        model = Property
        fields = ['id', 'parent_hotel_group', 'hotel_nick_name', 'manager_name', 'hotel_phone_number',
                  'hotel_website', 'number_of_rooms', 'check_in_time', 'check_out_time', 'location',
                  'nearby_popular_landmark', 'property_type', 'room_types', 'pet_friendly', 'breakfast_included',
                  'is_cancellation', 'status', 'is_online', 'address', 'images', 'is_verified', 'average_ratings',
                  'hotel_class', 'cancellation_policy', 'room_inventory']


class OrderSummarySerializer(RoomInventorySerializer):
    property_name = serializers.SerializerMethodField()
    room_type = RoomTypeSerializer()

    def get_property_name(self, obj):
        return obj.property.owner.hotel_name

    class Meta:
        model = RoomInventory
        fields = ['id', 'default_price', 'property_name', 'children_capacity', 'room_type', 'is_verified', 'status']


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingHistory
        fields = ['num_of_rooms', 'amount', 'check_in_date', 'check_out_date']


class GuestDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = GuestDetail
        fields = ['no_of_adults', 'no_of_children', 'age_of_children']


class CombinedSerializer(serializers.Serializer):

    booking_detail = BookingSerializer()
    guest_detail = GuestDetailSerializer()

    def create(self, validated_data):
        booking_data = validated_data.get('booking_detail')
        guest_data = validated_data.get('guest_detail')
        booking_data['customer'] = self.context['request'].user
        property = self.context['property']
        room = self.context['room']
        order = self.context['order_id']
        transfer_id = self.context['transfer_id']
        booking = BookingHistory.objects.create(property=property,
                                                order_id=order,
                                                rooms=room,
                                                currency="INR",
                                                transfer_id=transfer_id,
                                                **booking_data)

        guest = GuestDetail.objects.create(**guest_data, booking=booking)
        return {'booking': booking, 'guest': guest}


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ratings
        exclude = ['customer', 'property']
