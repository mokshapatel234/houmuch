from django_filters import rest_framework as filters
from hotel.models import RoomInventory
from .utils import is_booking_overlapping


class RoomInventoryFilter(filters.FilterSet):
    room_type = filters.CharFilter(field_name='room_type__id', lookup_expr='exact', label='Room Type')
    bed_type = filters.CharFilter(field_name='bed_type__id', lookup_expr='exact', label='Bed Type')
    bathroom_type = filters.CharFilter(field_name='bathroom_type__id', lookup_expr='exact', label='Bathroom Type')
    room_features = filters.CharFilter(field_name='room_features__id', lookup_expr='exact', label='Room Feature')
    common_amenities = filters.CharFilter(field_name='common_amenities__id', lookup_expr='exact', label='Common Amenity')
    max_price = filters.NumberFilter(method='filter_by_price', lookup_expr='exact', label='Max Price')
    min_price = filters.NumberFilter(method='filter_by_price', lookup_expr='exact', label='Min Price')
    check_in_date = filters.DateFilter(method='bookings_check', lookup_expr='exact', label='Check In Date')
    check_out_date = filters.DateFilter(method='bookings_check', lookup_expr='exact', label='Check Out Date')

    class Meta:
        model = RoomInventory
        fields = ['room_type', 'bed_type', 'bathroom_type', 'room_features', 'common_amenities', 'min_price',
                  'max_price', 'check_in_date', 'check_out_date']

    def filter_by_price(self, queryset, name, value):
        if self.data.get('min_price') and self.data.get('max_price'):
            queryset = queryset.filter(default_price__gte=self.data.get('min_price'), default_price__lte=self.data.get('max_price'))
        return queryset

    def bookings_check(self, queryset, name, value):
        if self.data.get('check_in_date') and self.data.get('check_out_date') and self.data.get('num_of_rooms'):
            queryset = is_booking_overlapping(queryset, self.data.get('check_in_date'),
                                              self.data.get('check_out_date'),
                                              self.data.get('num_of_rooms'),
                                              room_list=True)
            excluded_room_ids = []
            adjusted_availability = {
                room_inventory.id: {
                    'available_rooms': min(
                        room_inventory.available_rooms,
                        room_inventory.adjusted_min_rooms if room_inventory.adjusted_min_rooms is not None else room_inventory.available_rooms
                    ),
                    'effective_price': getattr(room_inventory, 'effective_price', room_inventory.default_price)  # Use effective_price if available, otherwise default_price
                }
                for room_inventory in queryset
            }
            for key, value in self.request.session.items():
                if key.startswith('room_id_'):
                    session_room_id = int(key.split('_')[-1])
                    session_num_of_rooms = value.get('num_of_rooms', 0)
                    if session_room_id in adjusted_availability:
                        new_availability = adjusted_availability[session_room_id]['available_rooms'] - session_num_of_rooms
                        adjusted_availability[session_room_id]['available_rooms'] = new_availability
                        if new_availability < int(self.data.get('num_of_rooms')):
                            excluded_room_ids.append(session_room_id)
            if excluded_room_ids:
                queryset = queryset.exclude(id__in=excluded_room_ids)
            self.request.adjusted_availability = adjusted_availability
            # self.request.effective_price = effective_price
            return queryset
