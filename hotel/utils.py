import jwt
from datetime import datetime, timedelta
from rest_framework.response import Response
import random
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from hotel_app_backend.messages import EXCEPTION_MESSAGE
from django.core.cache import cache


def generate_token(id):
    payload = {
        'user_id': id,
        'exp': datetime.utcnow() + timedelta(days=1)
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


def send_otp_email(email, otp, subject, template_name):
    try:
        html_message = render_to_string(template_name, {'otp': otp})
        to_email = [email]

        email_message = EmailMultiAlternatives(subject, body=None, to=to_email)
        email_message.attach_alternative(html_message, "text/html")
        email_message.send()

    except Exception:
        response_data = {
            "result": False,
            "message": EXCEPTION_MESSAGE,
        }
        return Response(response_data, status=400)


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
