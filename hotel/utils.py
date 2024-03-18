import jwt
from datetime import datetime, timedelta
from rest_framework.response import Response
import random
from django.template.loader import render_to_string
from django.core.cache import cache
from hotel_app_backend.boto_utils import ses_client
from django.conf import settings
from django.utils import timezone


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


def get_start_end_dates(num_of_days=None, num_of_weeks=None, num_of_months=None):
    start_date = timezone.now()
    end_date = None
    if num_of_days == 1:
        pass
    elif num_of_days:
        end_date = start_date + timedelta(days=num_of_days)
    elif num_of_weeks:
        end_date = start_date + timedelta(weeks=num_of_weeks)
    elif num_of_months:
        end_date = start_date + timedelta(days=30 * num_of_months)
    return start_date, end_date
