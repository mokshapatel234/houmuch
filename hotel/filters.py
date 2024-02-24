from django_filters import rest_framework as filters
from .models import RoomInventory


class RoomInventoryFilter(filters.FilterSet):
    room_type = filters.CharFilter(field_name='room_type__id', lookup_expr='exact', label='Room Type')

    class Meta:
        model = RoomInventory
        fields = ['room_type']
