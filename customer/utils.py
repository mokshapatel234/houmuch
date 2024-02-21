import jwt
from datetime import datetime, timedelta
from hotel.models import BookingHistory
from hotel.serializer import RoomInventoryOutSerializer
from hotel.models import RoomInventory
from django.conf import settings
from django.db.models import Exists, OuterRef


def generate_token(id):
    payload = {
        'user_id': id,
        'exp': datetime.utcnow() + timedelta(days=30)
    }
    jwt_token = jwt.encode(payload, 'secret', algorithm='HS256')
    return jwt_token


def is_booking_overlapping(room_inventory_query, start_date, end_date, message=False):
    overlapping_bookings_subquery = BookingHistory.objects.filter(
        rooms=OuterRef('pk'),
        check_out_date__gte=start_date,
        check_in_date__lte=end_date,
        book_status=True
    )
    room_inventory_query = room_inventory_query.annotate(
        has_overlapping_booking=Exists(overlapping_bookings_subquery)
    )
    non_overlapping_rooms = room_inventory_query.filter(has_overlapping_booking=False)

    if message:
        overlapping_rooms = room_inventory_query.filter(has_overlapping_booking=True)
        overlapping_room_ids = set(overlapping_rooms.values_list('id', flat=True))
        return overlapping_room_ids, non_overlapping_rooms

    return non_overlapping_rooms


def min_default_price(property_obj):
    room_inventories = property_obj.room_inventory
    default_prices = [room["default_price"] for room in room_inventories if room["default_price"] is not None]
    return min(default_prices) if default_prices else float('inf')


def get_room_inventory(property, num_of_rooms, min_price, max_price,
                       is_preferred_property_type, property_list, room_type,
                       start_date, end_date, session):
    room_ids = [int(key.split('_')[-1]) for key in session.keys() if key.startswith('room_id_')]
    room_inventory_query = RoomInventory.objects.filter(property=property).order_by('default_price')

    if room_type is not None:
        room_inventory_query = room_inventory_query.filter(room_type__id=room_type)

    if min_price is not None:
        room_inventory_query = room_inventory_query.filter(default_price__gte=float(min_price))
    if max_price is not None:
        room_inventory_query = room_inventory_query.filter(default_price__lte=float(max_price))
    if start_date is not None and end_date is not None:
        room_inventory_query = is_booking_overlapping(room_inventory_query, start_date, end_date)
    room_inventory_instances = list(room_inventory_query)

    include_property = len(room_inventory_instances) > 0

    is_preferred_type = property.property_type.id in settings.PREFERRED_PROPERTY_TYPES

    if all(room.id in room_ids for room in room_inventory_instances):
        include_property = False

    room_inventory_instances = [room for room in room_inventory_instances if room.id not in room_ids]

    if num_of_rooms is not None and len(room_inventory_instances) < num_of_rooms:
        include_property = False
    if include_property:
        if is_preferred_type or is_preferred_property_type:
            room_inventory_instances = room_inventory_instances
        elif num_of_rooms is not None and num_of_rooms > 0:
            room_inventory_instances = room_inventory_instances[:num_of_rooms]
        else:
            room_inventory_instances = room_inventory_instances[:1]

        property.room_inventory = [RoomInventoryOutSerializer(room_instance).data for room_instance in room_inventory_instances]
        property_list.append(property)

    return property_list


def booking_overlapping(room_inventory_query, start_date, end_date):
    print(room_inventory_query)
    overlapping_bookings = BookingHistory.objects.filter(
        check_in_date=start_date,
        check_out_date=end_date,
        rooms__in=room_inventory_query,
        book_status=True
    )
    print(overlapping_bookings)
    return overlapping_bookings
