import jwt
from datetime import datetime, timedelta
from hotel.models import BookingHistory, UpdateInventoryPeriod
from hotel.models import RoomInventory
from .serializer import RoomInventorySerializer
from django.db.models import IntegerField, Subquery, OuterRef, F, Sum, Value, Q, Min, Avg, Case, When, FloatField, Exists
from django.db.models.functions import Coalesce
from django.db.models import Func


class Round(Func):
    function = 'ROUND'
    template = '%(function)s(%(expressions)s, 2)'


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


def calculate_avg_price(room_inventory_qs, start_date, end_date):
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    room_adjustments = {}
    for room_inventory in room_inventory_qs:
        total_price = 0
        total_days = (end_date - start_date).days + 1
        for single_date in (start_date + timedelta(days=n) for n in range(total_days)):
            updates = UpdateInventoryPeriod.objects.filter(
                room_inventory=room_inventory,
                date__date__lte=single_date,
                date__date__gte=single_date,
                status=True,
                is_deleted=False
            ).aggregate(Avg('default_price'))
            daily_price = updates['default_price__avg'] if updates['default_price__avg'] is not None else room_inventory.default_price
            total_price += daily_price
        avg_price = total_price / total_days
        room_adjustments[room_inventory.id] = {'avg_price': avg_price}
    return room_adjustments


def is_booking_overlapping(room_inventory_query, start_date, end_date, num_of_rooms, room_list=False):
    total_booked_subquery = BookingHistory.objects.filter(
        rooms=OuterRef('pk'),
        check_out_date__date__gte=start_date,
        check_in_date__date__lte=end_date,
        book_status=True,
        is_cancel=False
    ).values('rooms').annotate(total_booked=Sum('num_of_rooms')).values('total_booked')
    total_booked_subquery = Subquery(total_booked_subquery[:1], output_field=IntegerField())
    adjusted_min_rooms_subquery = Subquery(
        UpdateInventoryPeriod.objects.filter(
            room_inventory_id=OuterRef('pk'),
            date__date__gte=start_date,
            date__date__lte=end_date,
            status=True,
            is_deleted=False
        ).values('room_inventory_id')
        .annotate(min_rooms_over_period=Min('num_of_rooms'))
        .values('min_rooms_over_period')[:1],
        output_field=IntegerField()
    )
    room_inventory_query = room_inventory_query.annotate(
        total_booked=Coalesce(total_booked_subquery, Value(0)),
        available_rooms=F('num_of_rooms') - Coalesce(total_booked_subquery, Value(0)),
        adjusted_min_rooms=Coalesce(adjusted_min_rooms_subquery, F('num_of_rooms'))
    ).exclude(Exists(UpdateInventoryPeriod.objects.filter(
        room_inventory_id=OuterRef('pk'),
        date__date__gte=start_date,
        date__date__lte=end_date,
        status=False,
        is_deleted=False
    )))
    # for room_inventory in room_inventory_query:
    #     print(f"room ID: {room_inventory.id}")
    #     print(f"Total Booked: {room_inventory.total_booked}")
    #     print(f"Available Rooms: {room_inventory.available_rooms}")
    #     print(f"Adjusted Minimum Rooms: {room_inventory.adjusted_min_rooms}")
    #     print("------------------")

    # room_inventory_query = room_inventory_query.filter(
    #     Q(available_rooms__gte=F('adjusted_min_rooms')) | Q(adjusted_min_rooms__isnull=True),
    #     available_rooms__gte=num_of_rooms
    # ).order_by('default_price', '-available_rooms')

    room_adjustments = calculate_avg_price(room_inventory_query, start_date, end_date)
    valid_room_ids = [room_id for room_id, adjustments in room_adjustments.items() if adjustments['avg_price'] is not None]
    room_inventory_query = room_inventory_query.filter(id__in=valid_room_ids)
    room_inventory_query = room_inventory_query.annotate(
        effective_price=Round(
            Case(
                *[When(id=room_id, then=Value(adjustments['avg_price'])) for room_id, adjustments in room_adjustments.items()],
                default=F('default_price'),
                output_field=FloatField()
            ),
            output_field=FloatField()
        )
    )
    if room_list:
        return room_inventory_query
    return room_inventory_query.first()


def get_room_inventory(property, property_list, num_of_rooms, min_price, max_price, room_type,
                       check_in_date, check_out_date, num_of_adults, num_of_children, high_to_low, session):
    room_inventory_query = RoomInventory.objects.filter(property=property, is_verified=True, status=True
                                                        )
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
    available_room_inventory = is_booking_overlapping(room_inventory_query, check_in_date, check_out_date, num_of_rooms, room_list=True).order_by('effective_price')
    adjusted_availability = {
        room_inventory.id: {
            'available_rooms': min(
                room_inventory.available_rooms,
                room_inventory.adjusted_min_rooms if room_inventory.adjusted_min_rooms is not None else room_inventory.available_rooms
            ),
            'effective_price': getattr(room_inventory, 'effective_price', room_inventory.default_price),
            'adult_capacity': room_inventory.adult_capacity,
            'children_capacity': room_inventory.children_capacity
        }
        for room_inventory in available_room_inventory
    }
    for key, value in session.items():
        if key.startswith('room_id_'):
            session_room_id = int(key.split('_')[-1])
            session_num_of_rooms = value.get('num_of_rooms', 0)
            if session_room_id in adjusted_availability:
                adjusted_availability[session_room_id]['available_rooms'] -= session_num_of_rooms
                adjusted_availability[session_room_id]['available_rooms'] = max(0, adjusted_availability[session_room_id]['available_rooms'])
    available_room_inventory = [
        room_inventory for room_inventory in available_room_inventory
        if room_inventory.id in adjusted_availability
        and adjusted_availability[room_inventory.id]['available_rooms'] >= num_of_rooms
        and adjusted_availability[room_inventory.id]['adult_capacity'] * num_of_rooms >= num_of_adults
        and adjusted_availability[room_inventory.id]['children_capacity'] * num_of_rooms >= num_of_children
    ]
    include_property = False
    if available_room_inventory:
        room_inventory_instance = available_room_inventory[0]
        serialized_data = RoomInventorySerializer(room_inventory_instance, context={"start_date": check_in_date, "end_date": check_out_date}).data
        serialized_data['available_rooms'] = adjusted_availability[room_inventory_instance.id]['available_rooms']
        serialized_data['default_price'] = round(adjusted_availability[room_inventory_instance.id]['effective_price'])
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
        date__date__gte=check_in_date,
        date__date__lte=check_out_date
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
    current_time = datetime.now().time()
    if current_time > check_in_time:
        days_before_check_in -= 1
    cancellation_charge_percentage = cancellation_policies.last().cancellation_percents
    for policy in sorted(cancellation_policies, key=lambda x: x.cancellation_days):
        if days_before_check_in <= policy.cancellation_days:
            cancellation_charge_percentage = policy.cancellation_percents
            break
    return cancellation_charge_percentage
