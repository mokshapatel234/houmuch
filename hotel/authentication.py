from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from .models import Owner
from hotel_app_backend.messages import INVALID_TOKEN_MESSAGE, TOKEN_REQUIRED_MESSAGE, OWNER_NOT_FOUND_MESSAGE
import jwt


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        jwt_token = request.headers.get('Authorization', None)

        if jwt_token:
            try:
                payload = jwt.decode(jwt_token, 'secret', algorithms=['HS256'])
            except (jwt.DecodeError, jwt.ExpiredSignatureError):
                raise exceptions.AuthenticationFailed(INVALID_TOKEN_MESSAGE)
        else:
            raise exceptions.AuthenticationFailed(TOKEN_REQUIRED_MESSAGE)

        try:
            request.user = Owner.objects.get(id=payload['user_id'])
        except Owner.DoesNotExist:
            raise exceptions.AuthenticationFailed(OWNER_NOT_FOUND_MESSAGE)

        return (request.user, jwt_token)
