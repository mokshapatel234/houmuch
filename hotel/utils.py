import jwt
from datetime import datetime, timedelta
from rest_framework.response import Response
import random
from django.template.loader import render_to_string
from django.core.cache import cache
from hotel_app_backend.boto_utils import ses_client
from django.conf import settings
from django.utils import timezone
import copy
from .models import UpdateInventoryPeriod, UpdateType, UpdateRequest
from dateutil import parser
from django.utils.timezone import now
import calendar
from collections import defaultdict
from django.db.models import F, Func
from .serializer import UpdateInventoryPeriodSerializer


def generate_token(id):
    payload = {
        'user_id': id,
        'exp': datetime.utcnow() + timedelta(days=30)
    }

    jwt_token = jwt.encode(payload, 'secret', algorithm='HS256')

    return jwt_token


def model_name_to_snake_case(name):
    return ''.join(['_' + i.lower() if i.isupper() else i for i in name]).lstrip('_')


def generate_response(instance, message, status_code, serializer_class=None):
    if serializer_class:
        serializer = serializer_class(instance)
    response_data = {
        'result': True,
        'data': serializer.data if serializer_class else instance,
        'message': message,
    }
    return Response(response_data, status=status_code)


def error_response(message, status_code):
    response_data = {
        'result': False,
        'message': message,
    }
    return Response(response_data, status=status_code)


def deletion_success_response(message, status_code):
    response_data = {
        'result': True,
        'message': message,
    }
    return Response(response_data, status=status_code)


def generate_otp():
    return str(random.randint(1000, 9999))


def send_mail(data):
    html_message = render_to_string(data["template"], data["context"])
    response = ses_client.send_email(
        Source=settings.DEFAULT_FROM_EMAIL,
        Destination={
            'ToAddresses': [data["email"]]
        },
        Message={
            'Subject': {
                'Data': data["subject"],
            },
            'Body': {
                'Html': {
                    'Data': html_message,
                }
            }
        }
    )
    return response


def check_plan_expiry(instance):
    plan_duration_months = instance.subscription_plan.duration
    plan_end_date = instance.created_at + timedelta(days=30 * plan_duration_months)
    current_date = timezone.now()
    if current_date > plan_end_date:
        return True
    return False


def remove_cache(name, user):
    cache_key = f"{name}_{user.id}"
    cache.delete(cache_key)


def cache_response(name, user):
    cache_key = f"{name}_{user.id}"
    cached_data = cache.get(cache_key)
    if cached_data:
        return Response(cached_data)


def set_cache(name, user, data):
    cache_key = f"{name}_{user.id}"
    cache.set(cache_key, data, timeout=60 * 5)


def generate_date_range(start_date, end_date):
    for n in range(int((end_date - start_date).days) + 1):
        yield start_date + timedelta(n)
    return start_date, end_date


def update_period(updated_period_data, instance):
    dates = updated_period_data.pop('dates', [])
    removed_dates = updated_period_data.pop('removed_dates', [])
    type_id = updated_period_data['type']
    if dates:
        dates_str = ', '.join(dates)
        update_request = UpdateRequest(request=dates_str)
        update_request.save()

    new_periods = []
    update_map = {}
    if not dates and type_id == 1:
        dates = [now().date()]
    if 'type' in updated_period_data:
        updated_period_data['type'] = UpdateType.objects.get(id=type_id)
        if type_id == 3 and dates:
            all_dates_within_ranges = []
            sorted_dates = sorted(parser.parse(date).date() for date in dates)
            for i in range(0, len(sorted_dates), 2):
                if i + 1 < len(sorted_dates):
                    start_date, end_date = sorted_dates[i], sorted_dates[i + 1]
                    all_dates_within_ranges.extend(generate_date_range(start_date, end_date))
            dates = all_dates_within_ranges
    for date in dates:
        updated_period_data_copy = copy.deepcopy(updated_period_data)
        updated_period_data_copy['date'] = date
        existing_instance = UpdateInventoryPeriod.objects.filter(date=date, room_inventory=instance).first()
        if existing_instance:
            for key, value in updated_period_data_copy.items():
                setattr(existing_instance, key, value)
            update_map[existing_instance.id] = existing_instance
        else:
            new_periods.append(UpdateInventoryPeriod(room_inventory=instance, request=update_request, **updated_period_data_copy))
    if new_periods:
        UpdateInventoryPeriod.objects.bulk_create(new_periods)
    if update_map:
        UpdateInventoryPeriod.objects.bulk_update(update_map.values(), updated_period_data_copy.keys())
    if removed_dates and type_id == 3:
        payload_removed_dates_set = set(removed_dates)
        print(payload_removed_dates_set, "REMMMOVVVED")
        processed_removed_dates = []
        for i in range(0, len(removed_dates), 2):
            start_date = parser.parse(removed_dates[i]).date()
            end_date = parser.parse(removed_dates[i + 1]).date() if i + 1 < len(removed_dates) else start_date
            processed_removed_dates.extend(generate_date_range(start_date, end_date))
        removed_dates = [date.strftime('%Y-%m-%d') for date in processed_removed_dates]

        instances_to_mark_deleted = UpdateInventoryPeriod.objects.filter(
            room_inventory=instance,
            date__in=[parser.parse(date).date() for date in removed_dates]
        )
        instances_to_mark_deleted.update(is_deleted=True, deleted_at=datetime.now())
        update_requests_to_check = {instance.request for instance in instances_to_mark_deleted}
        for update_request in update_requests_to_check:
            current_dates = set(update_request.request.split(', '))
            if current_dates == payload_removed_dates_set:
                update_request.is_deleted = True
                update_request.deleted_at = datetime.now()
                update_request.save()
            else:
                updated_dates = current_dates - payload_removed_dates_set
                update_request.request = ', '.join(sorted(updated_dates))
                update_request.save()


def get_days_before_check_in(booking, days_before_check_in):
    check_in_time_str = booking.property.check_in_time
    current_time = datetime.now().time()
    check_in_time = datetime.strptime(check_in_time_str, "%I:%M %p").time()
    if current_time > check_in_time:
        days_before_check_in -= 1
    return days_before_check_in


def find_month_year(month_year, grouped_data):
    for item in grouped_data:
        if item['month_year'] == month_year:
            return item
    return None


def get_updated_inventory(room_inventory, start_date, end_date):
    updated_inventory = UpdateInventoryPeriod.objects.filter(room_inventory=room_inventory,
                                                             date__range=(start_date, end_date),
                                                             is_deleted=False).select_related(
        'request', 'type').annotate(
        month=Func(F('date'), function='EXTRACT', template="%(function)s(MONTH from %(expressions)s)"),
        year=Func(F('date'), function='EXTRACT', template="%(function)s(YEAR from %(expressions)s)"),
    ).order_by('year', 'month', 'type')

    grouped_data = []
    multi_range_data = []

    for item in updated_inventory:
        if item.type_id == 3 and item.request:
            request_id_group = next((g for g in multi_range_data if g.get('request_id') == item.request_id), None)
            if not request_id_group:
                request_details = item.request.request if item.request else "Unknown Request"
                request_id_group = {
                    'request_id': item.request_id,
                    'request_details': request_details
                }
                multi_range_data.append(request_id_group)
            serialized_item = UpdateInventoryPeriodSerializer(item).data
        else:
            month_year = f"{calendar.month_name[int(item.month)]} {int(item.year)}"
            month_year_group = next((g for g in grouped_data if g.get('month_year') == month_year), None)
            if not month_year_group:
                month_year_group = {'month_year': month_year, 'types': defaultdict(list)}
                grouped_data.append(month_year_group)
            serialized_item = UpdateInventoryPeriodSerializer(item).data
            month_year_group['types'][item.type.type].append(serialized_item)

    for group in grouped_data:
        group['types'] = dict(group['types'])

    return {
        'regular_updates': grouped_data,
        'multi_range_updates': multi_range_data
    }
