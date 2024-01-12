from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Customer
from hotel.models import FCMToken
from .serializer import *
from .utils import generate_token
from hotel_app_backend.messages import *

class CustomerRegisterView(APIView):
    permission_classes = (permissions.AllowAny, )

    def post(self, request):
        try:
            serializer = RegisterSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            phone_number = serializer.validated_data.get('phone_number')
            fcm_token = request.data.get('fcm_token')

            if not phone_number:
                return Response(PHONE_REQUIRED_MESSAGE, status=status.HTTP_400_BAD_REQUEST)

            if Customer.objects.filter(phone_number=phone_number).exists():
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


class CustomerLoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            phone = serializer.validated_data.get('phone_number')
            fcm_token = request.data.get('fcm_token')

            try:
                customer = Customer.objects.get(phone_number=phone)
                if customer.is_verified:
                    if fcm_token:
                        FCMToken.objects.create(user_id=customer.id, fcm_token=fcm_token, is_owner=True)

                    token = generate_token(customer.id)
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

            except Customer.DoesNotExist:
                return Response(NOT_REGISTERED_MESSAGE, status=status.HTTP_400_BAD_REQUEST)

        except Exception:
            return Response(EXCEPTION_MESSAGE, status=status.HTTP_400_BAD_REQUEST)