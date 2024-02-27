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
    check_in_date = filters.DateTimeFilter(method='bookings_check', lookup_expr='exact', label='Check In Date')
    check_out_date = filters.DateTimeFilter(method='bookings_check', lookup_expr='exact', label='Check Out Date')

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
            return is_booking_overlapping(queryset, self.data.get('check_in_date'),
                                          self.data.get('check_out_date'),
                                          self.data.get('num_of_rooms'),
                                          room_list=True)
