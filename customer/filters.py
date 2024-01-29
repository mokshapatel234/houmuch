from django_filters import rest_framework as filters
from django.contrib.gis.measure import D
from django.contrib.gis.geos import Point
from hotel.models import Property


class PropertyFilter(filters.FilterSet):
    latitude = filters.NumberFilter(field_name='location', method='filter_by_distance', label='Latitude')
    longitude = filters.NumberFilter(method='filter_by_distance', label='Longitude')
    nearby_popular_landmark = filters.CharFilter(lookup_expr='icontains', label='Nearby Popular Landmark')
    room_type = filters.CharFilter(field_name='room_types__room_type', lookup_expr='exact', label='Room Type')

    class Meta:
        model = Property
        fields = ['latitude', 'longitude', 'nearby_popular_landmark', 'room_type']

    def filter_by_distance(self, queryset, name, value):
        if self.data.get('latitude') and self.data.get('longitude'):
            point = Point(float(self.data['longitude']), float(self.data['latitude']), srid=4326)
            return queryset.filter(location__distance_lte=(point, D(m=1000)))
        return queryset
