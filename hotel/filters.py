from django_filters import rest_framework as filters
from .models import RoomInventory, BookingHistory
from django.utils import timezone


class RoomInventoryFilter(filters.FilterSet):
    room_type = filters.CharFilter(field_name='room_type__id', lookup_expr='exact', label='Room Type')

    class Meta:
        model = RoomInventory
        fields = ['room_type']


class BookingFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name="check_in_date__date", lookup_expr='gte')
    end_date = filters.DateFilter(field_name="check_in_date__date", lookup_expr='lte')
    is_confirmed = filters.BooleanFilter(field_name="is_confirmed")
    is_cancel = filters.BooleanFilter(field_name='is_cancel')
    is_today = filters.BooleanFilter(method='filter_by_is_today')

    class Meta:
        model = BookingHistory
        fields = ['start_date', 'end_date', 'is_confirmed', 'is_cancel', 'is_today']

    def filter_by_is_today(self, queryset, name, value):
        today = timezone.now().date()
        if value:
            return queryset.filter(check_in_date__date=today)
        else:
            return queryset.exclude(check_in_date__date=today)


class TransactionFilter(filters.FilterSet):
    is_completed = filters.BooleanFilter(field_name="book_status")

    class Meta:
        model = BookingHistory
        fields = ['is_completed']
