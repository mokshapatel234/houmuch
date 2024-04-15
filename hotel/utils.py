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

    dates_str = ', '.join(dates)
    update_request = UpdateRequest(request=dates_str)
    update_request.save()

    new_periods = []
    update_map = {}
    if not dates:
        dates = [now().date()]
    if 'type' in updated_period_data:
        type_id = updated_period_data['type']
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
    if removed_dates:
        removed_dates = [parser.parse(date).date() if isinstance(date, str) else date for date in removed_dates]
        instances_to_mark_deleted = UpdateInventoryPeriod.objects.filter(
            room_inventory=instance,
            date__in=removed_dates
        )
        instances_to_mark_deleted.update(is_deleted=True, deleted_at=now())


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
