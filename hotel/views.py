from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Owner, FCMToken
from .serializer import *
from .utils import generate_token
from hotel_app_backend.messages import *

class HotelRegisterView(APIView):
    permission_classes = (permissions.AllowAny, )

    def post(self, request):
        try:
            serializer = RegisterSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            phone_number = serializer.validated_data.get('phone_number')
            fcm_token = request.data.get('fcm_token')

            if not phone_number:
                return Response(PHONE_REQUIRED_MESSAGE, status=status.HTTP_400_BAD_REQUEST)

            if Owner.objects.filter(phone_number=phone_number).exists():
                return Response(PHONE_ALREADY_PRESENT_MESSAGE, status=status.HTTP_400_BAD_REQUEST)
             
            else:
                serializer.save()
                user_id = serializer.instance.id

                if fcm_token:
                    FCMToken.objects.create(user_id=user_id, fcm_token=fcm_token, is_owner=True)

                token = generate_token(user_id)

                response_data = {
                    **REGISTRATION_SUCCESS_MESSAGE,
                    'data': {
                        'first_name': serializer.data['first_name'],
                        'token': token,
                    },
                }
                return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception:
            return Response(EXCEPTION_MESSAGE, status=status.HTTP_400_BAD_REQUEST)


class HotelLoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            phone = serializer.validated_data.get('phone_number')
            fcm_token = request.data.get('fcm_token')

            try:
                hotel_owner = Owner.objects.get(phone_number=phone)
                if hotel_owner.is_verified:
                    if fcm_token:
                        FCMToken.objects.create(user_id=hotel_owner.id, fcm_token=fcm_token, is_owner=True)

                    token = generate_token(hotel_owner.id)
                    response_data = {
                        **LOGIN_SUCCESS_MESSAGE,
                        'data': {
                            'PhoneNumber': phone,
                            'token': token,
                        },
                    }
                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    return Response(OWNER_NOT_VERIFIED_MESSAGE, status=status.HTTP_400_BAD_REQUEST)

            except Owner.DoesNotExist:
                return Response(NOT_REGISTERED_MESSAGE, status=status.HTTP_400_BAD_REQUEST)

        except Exception:
            return Response(EXCEPTION_MESSAGE, status=status.HTTP_400_BAD_REQUEST)