from django_filters import rest_framework as filters
from .models import RoomInventory, BookingHistory, PropertyDeal
from django.utils import timezone


class RoomInventoryFilter(filters.FilterSet):
    room_type = filters.CharFilter(field_name='room_type__id', lookup_expr='exact', label='Room Type')

    class Meta:
        model = RoomInventory
        fields = ['room_type']


class BookingFilter(filters.FilterSet):
    start_date = filters.DateFilter(field_name="check_in_date__date", lookup_expr='gte')
    end_date = filters.DateFilter(field_name="check_in_date__date", lookup_expr='lte')
    is_complete = filters.BooleanFilter(method="filter_by_is_complete")
    is_cancel = filters.BooleanFilter(method='filter_by_is_cancel')
    is_today = filters.BooleanFilter(method='filter_by_is_today')

    class Meta:
        model = BookingHistory
        fields = ['start_date', 'end_date', 'is_complete', 'is_cancel', 'is_today']

    def filter_by_is_today(self, queryset, name, value):
        today = timezone.now().date()
        if value:
            return queryset.filter(check_in_date__date=today)
        else:
            return queryset.exclude(check_in_date__date=today)

    def filter_by_is_cancel(self, queryset, name, value):
        if value:
            return queryset.filter(is_cancel=True)
        else:
            return queryset.exclude(is_cancel=True)

    def filter_by_is_complete(self, queryset, name, value):
        today = timezone.now().date()
        if value:
            return queryset.filter(check_out_date__date__lt=today)
        else:
            return queryset.exclude(check_out_date__date__lt=today)


class TransactionFilter(filters.FilterSet):
    is_completed = filters.BooleanFilter(field_name="book_status")

    class Meta:
        model = BookingHistory
        fields = ['is_completed']


class PropertyDealFilter(filters.FilterSet):
    is_active = filters.BooleanFilter(method='filter_by_is_active')
    is_confirm = filters.BooleanFilter(method='filter_by_is_confirm')

    class Meta:
        model = PropertyDeal
        fields = ['is_active', 'is_confirm']

    def filter_by_is_active(self, queryset, name, value):
        if value:
            return queryset.filter(is_active=True)
        else:
            return queryset.filter(is_active=False, session__is_open=True)

    def filter_by_is_confirm(self, queryset, name, value):
        if value:
            return queryset.filter(is_winning_bid=True)
        else:
            return queryset.filter(is_winning_bid=False, session__is_open=False)
