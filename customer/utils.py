import jwt
from datetime import datetime, timedelta
from hotel.models import BookingHistory, UpdateInventoryPeriod
from hotel.models import RoomInventory
from .serializer import RoomInventorySerializer
from django.db.models import IntegerField, Subquery, OuterRef, F, Sum, Exists, Value, Q
from django.db.models.functions import Coalesce


def generate_token(id):
    payload = {
        'user_id': id,
        'exp': datetime.utcnow() + timedelta(days=30)
    }
    jwt_token = jwt.encode(payload, 'secret', algorithm='HS256')
    return jwt_token


def sort_properties_by_price(property_obj, high_to_low=False):
    room_inventory = property_obj.room_inventory
    if room_inventory and "default_price" in room_inventory:
        price = room_inventory["default_price"]
    else:
        price = float('inf')
    return -price if high_to_low else price


def is_booking_overlapping(room_inventory_query, start_date, end_date, num_of_rooms, room_list=False):
    exclusion_filter = UpdateInventoryPeriod.objects.filter(
        Q(end_date__date__gte=start_date) | Q(end_date__isnull=True),
        room_inventory=OuterRef('pk'),
        start_date__date__lte=end_date,
        status=False
    )
    room_inventory_query = room_inventory_query.annotate(
        exclude_due_to_update=Exists(exclusion_filter)
    ).filter(exclude_due_to_update=False)
    update_period_filter = UpdateInventoryPeriod.objects.filter(
        Q(end_date__date__gte=start_date) | Q(end_date__isnull=True),
        room_inventory=OuterRef('pk'),
        start_date__date__lte=end_date,
        status=True
    ).values('num_of_rooms')
    room_inventory_query = room_inventory_query.annotate(
        adjusted_num_of_rooms=Coalesce(Subquery(update_period_filter[:1]), F('num_of_rooms'))
    )
    total_booked_subquery = BookingHistory.objects.filter(
        rooms=OuterRef('pk'),
        check_out_date__date__gte=start_date,
        check_in_date__date__lte=end_date,
        book_status=True,
        is_cancel=False
    ).annotate(total=Sum('num_of_rooms')).values('total')[:1]
    room_inventory_query = room_inventory_query.annotate(
        total_booked=Coalesce(Subquery(total_booked_subquery, output_field=IntegerField()), Value(0))
    )
    room_inventory_query = room_inventory_query.annotate(
        available_rooms=F('adjusted_num_of_rooms') - F('total_booked')
    ).filter(available_rooms__gte=num_of_rooms)

    if room_list:
        return room_inventory_query
    return room_inventory_query.first()


def get_room_inventory(property, property_list, num_of_rooms, min_price, max_price, room_type,
                       check_in_date, check_out_date, num_of_adults, num_of_children, high_to_low, session):
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
        current_datetime = datetime.now().date()
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
        serialized_data = RoomInventorySerializer(room_inventory_instance, context={"start_date": check_in_date, "end_date": check_out_date}).data
        serialized_data['available_rooms'] = adjusted_availability[room_inventory_instance.id]
        property.room_inventory = serialized_data
        include_property = True
        if property_list is not None and include_property:
            property_list.append(property)
    return property_list if property_list is not None else property


def calculate_available_rooms(room, check_in_date, check_out_date, session):
    total_booked = BookingHistory.objects.filter(
        rooms=room,
        check_out_date__date__gte=check_in_date,
        check_in_date__date__lte=check_out_date,
        book_status=True,
        is_cancel=False
    ).aggregate(total=Sum('num_of_rooms'))['total'] or 0
    updated_period = UpdateInventoryPeriod.objects.filter(
        room_inventory=room,
        start_date__date__lte=check_out_date,
    ).filter(
        Q(end_date__date__gte=check_in_date) | Q(end_date__isnull=True)
    ).first()
    if updated_period:
        available_rooms = updated_period.num_of_rooms - total_booked
    else:
        available_rooms = room.num_of_rooms - total_booked
    session_key = f'room_id_{room.id}'
    session_rooms_booked = session.get(session_key, {}).get('num_of_rooms', 0)
    return total_booked, available_rooms, session_rooms_booked


def get_cancellation_charge_percentage(cancellation_policies, days_before_check_in, check_in_time_str):
    check_in_time = datetime.strptime(check_in_time_str, "%I:%M %p").time()
    now = datetime.now()
    current_time = now.time()
    if current_time > check_in_time:
        days_before_check_in -= 1
    cancellation_charge_percentage = cancellation_policies.last().cancellation_percents
    for policy in sorted(cancellation_policies, key=lambda x: x.cancellation_days):
        if days_before_check_in <= policy.cancellation_days:
            cancellation_charge_percentage = policy.cancellation_percents
            break
    return cancellation_charge_percentage
