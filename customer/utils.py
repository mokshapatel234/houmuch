import jwt
from datetime import datetime, timedelta
from hotel.models import BookingHistory
from hotel.models import RoomInventory
from .serializer import RoomInventorySerializer
from django.db.models import IntegerField, Subquery, OuterRef, F, Sum
from django.db.models.functions import Coalesce


def generate_token(id):
    payload = {
        'user_id': id,
        'exp': datetime.utcnow() + timedelta(days=30)
    }
    jwt_token = jwt.encode(payload, 'secret', algorithm='HS256')
    return jwt_token


def min_default_price(property_obj):
    room_inventory = property_obj.room_inventory
    if room_inventory and "default_price" in room_inventory:
        return room_inventory["default_price"]
    else:
        return float('inf')


def is_booking_overlapping(room_inventory_query, start_date, end_date, num_of_rooms, message=False, room_list=False):
    total_booked_subquery = BookingHistory.objects.filter(
        rooms=OuterRef('pk'),
        check_out_date__gte=start_date,
        check_in_date__lte=end_date,
        book_status=True
    ).annotate(total=Sum('num_of_rooms')).values('total')

    room_inventory_query = room_inventory_query.annotate(
        total_booked=Coalesce(Subquery(total_booked_subquery, output_field=IntegerField()), 0),
        available_rooms=F('num_of_rooms') - Coalesce(Subquery(total_booked_subquery, output_field=IntegerField()), 0)
    ).filter(available_rooms__gte=num_of_rooms).order_by('default_price', '-available_rooms')
    if message:
        unavailable_room_inventories = room_inventory_query.filter(available_rooms__lt=num_of_rooms)
        unavailable_room_ids = set(unavailable_room_inventories.values_list('id', flat=True))
        available_room_inventories = room_inventory_query.exclude(id__in=unavailable_room_ids)
        return unavailable_room_ids, available_room_inventories.first() if available_room_inventories.exists() else None
    elif room_list:
        return room_inventory_query
    return room_inventory_query.first()


def get_room_inventory(property, property_list, num_of_rooms, min_price, max_price, room_type,
                       check_in_date, check_out_date, num_of_adults, num_of_children, session):
    room_inventory_query = RoomInventory.objects.filter(property=property, is_verified=True, status=True,
                                                        adult_capacity__gte=num_of_adults, children_capacity__gte=num_of_children
                                                        ).order_by('default_price')
    if room_type is not None:
        room_inventory_query = room_inventory_query.filter(room_type__id=room_type)
    if min_price is not None:
        room_inventory_query = room_inventory_query.filter(default_price__gte=float(min_price))
    if max_price is not None:
        room_inventory_query = room_inventory_query.filter(default_price__lte=float(max_price))
    if check_in_date is None or check_out_date is None:
        current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if check_in_date is None:
            check_in_date = current_datetime
        if check_out_date is None:
            check_out_date = current_datetime
    available_room_inventory = is_booking_overlapping(room_inventory_query, check_in_date, check_out_date, num_of_rooms, room_list=True)
    adjusted_availability = {room_inventory.id: room_inventory.available_rooms for room_inventory in available_room_inventory}
    for key, value in session.items():
        if key.startswith('room_id_'):
            session_room_id = int(key.split('_')[-1])
            session_num_of_rooms = value.get('num_of_rooms', 0)
            if session_room_id in adjusted_availability:
                adjusted_availability[session_room_id] = max(0, adjusted_availability[session_room_id] - session_num_of_rooms)
    available_room_inventory = [room_inventory for room_inventory in available_room_inventory if room_inventory.id in adjusted_availability and adjusted_availability[room_inventory.id] >= num_of_rooms]
    include_property = False
    if available_room_inventory:
        room_inventory_instance = available_room_inventory[0]
        serialized_data = RoomInventorySerializer(room_inventory_instance).data
        serialized_data['available_rooms'] = adjusted_availability[room_inventory_instance.id]
        property.room_inventory = serialized_data
        include_property = True
        if property_list is not None and include_property:
            property_list.append(property)
    return property_list if property_list is not None else property
