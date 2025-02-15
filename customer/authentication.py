from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from .models import Customer
from hotel_app_backend.messages import INVALID_TOKEN_MESSAGE, TOKEN_REQUIRED_MESSAGE, CUSTOMER_NOT_FOUND_MESSAGE, DEVICE_ID_ERROR_MESSAGE
import jwt


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        jwt_token = request.headers.get('Authorization', None)
        device_id = request.headers.get('Device-Id', None)
        if jwt_token:
            try:
                payload = jwt.decode(jwt_token, 'secret', algorithms=['HS256'])
            except (jwt.DecodeError, jwt.ExpiredSignatureError):
                raise exceptions.AuthenticationFailed(INVALID_TOKEN_MESSAGE)
        else:
            raise exceptions.AuthenticationFailed(TOKEN_REQUIRED_MESSAGE)
        try:
            request.user = Customer.objects.get(id=payload['user_id'])
        except Customer.DoesNotExist:
            raise exceptions.AuthenticationFailed(CUSTOMER_NOT_FOUND_MESSAGE)
        if device_id == request.user.device_id:
            return (request.user, jwt_token)
        else:
            raise exceptions.AuthenticationFailed(DEVICE_ID_ERROR_MESSAGE)
