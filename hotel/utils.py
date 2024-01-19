import jwt
from datetime import datetime, timedelta
from rest_framework.response import Response
import random
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def generate_token(id):
    payload = {
        'user_id': id,
        'exp': datetime.utcnow() + timedelta(days=1)
    }

    jwt_token = jwt.encode(payload, 'secret', algorithm='HS256')

    return jwt_token


def model_name_to_snake_case(name):
    return ''.join(['_' + i.lower() if i.isupper() else i for i in name]).lstrip('_')


def generate_response(instance, message, status_code, serializer_class):
    serializer = serializer_class(instance)
    response_data = {
        'result': True,
        'data': serializer.data,
        'message': message,
    }
    return Response(response_data, status=status_code)


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(email, otp, subject, template_name):
    try:
        html_message = render_to_string(template_name, {'otp': otp})

        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [email]

        email_message = EmailMultiAlternatives(subject, body=None, from_email=from_email, to=to_email)
        email_message.attach_alternative(html_message, "text/html")
        email_message.send()

        response_data = {
            "result": True,
            "message": "Email sent successfully",
            "otp": otp,
        }
        return Response(response_data)

    except Exception as e:
        response_data = {
            "result": False,
            "message": f"Something went wrong: {str(e)}",
        }
        return Response(response_data, status=400)