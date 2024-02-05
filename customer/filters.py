from django_filters import rest_framework as filters
from django.contrib.gis.measure import D
from django.contrib.gis.geos import Point
from hotel.models import Property, RoomInventory
from django.db.models import Subquery, OuterRef


class PropertyFilter(filters.FilterSet):
    # latitude = filters.NumberFilter(field_name='location', method='filter_by_distance', label='Latitude')
    # longitude = filters.NumberFilter(method='filter_by_distance', label='Longitude')
    nearby_popular_landmark = filters.CharFilter(lookup_expr='icontains', label='Nearby Popular Landmark')
    room_type = filters.CharFilter(field_name='room_types__room_type', lookup_expr='exact', label='Room Type')
    min_price = filters.NumberFilter(method='filter_by_price', lookup_expr='exact', label='Min Price')
    max_price = filters.NumberFilter(method='filter_by_price', lookup_expr='exact', label='Max Price')
    # num_of_rooms = filters.NumberFilter(method='filter_by_num_of_rooms', label='Number of Rooms')

    class Meta:
        model = Property
        fields = ['nearby_popular_landmark', 'room_type', 'min_price', 'max_price']

    def filter_by_distance(self, queryset, name, value):
        if self.data.get('latitude') and self.data.get('longitude'):
            point = Point(float(self.data['longitude']), float(self.data['latitude']), srid=4326)
            return queryset.filter(location__distance_lte=(point, D(m=1000)))
        return queryset
    
    def filter_by_price(self, queryset, name, value):
        if self.data.get('min_price') and self.data.get('max_price'):
            subquery = RoomInventory.objects.filter(
                property=OuterRef('pk')
            ).order_by('default_price').values('default_price')[:1]
            queryset = queryset.annotate(lowest_price=Subquery(subquery))
            queryset = queryset.filter(lowest_price__gte=self.data.get('min_price'), lowest_price__lte=self.data.get('max_price'))
        return queryset
        