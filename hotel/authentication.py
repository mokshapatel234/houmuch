from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from .models import *
import jwt
class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        jwt_token = request.headers.get('Authorization', None)

        if jwt_token:
            try:
                payload = jwt.decode(jwt_token, 'secret', algorithms=['HS256'])
            
            except (jwt.DecodeError, jwt.ExpiredSignatureError) as e:
                print(e)
                raise exceptions.AuthenticationFailed('Token is invalid')
        else:
            raise exceptions.AuthenticationFailed('Token is required')

        try:
            request.user = Owner.objects.get(id=payload['user_id'])    
        except Owner.DoesNotExist:
            raise exceptions.AuthenticationFailed('Hotel not found.')

        return (request.user, jwt_token)
