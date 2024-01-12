from rest_framework import  permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import HotelOwner, FCMToken
from .serializer import *
from .utils import generate_token


class HotelRegisterView(APIView):
    permission_classes = (permissions.AllowAny, )

    def post(self, request):
        try:
            serializer = RegisterSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            phone_number = serializer.validated_data.get('phone_number')
            fcm_token = request.data.get('fcm_token')

            if not phone_number:
                return Response({'result': False, 'message': 'phone number is required for registration.'}, status=status.HTTP_400_BAD_REQUEST)

            if HotelOwner.objects.filter(phone_number=phone_number).exists():
                return Response({'result': False, 'message': 'phone number is already present'}, status=status.HTTP_400_BAD_REQUEST)
             
            else:
                serializer.save()
                user_id = serializer.instance.id

                if fcm_token:
                    FCMToken.objects.create(user_id=user_id, fcm_token=fcm_token, is_owner=True)

                token = generate_token(user_id)

                response_data = {
                    'result': True,
                    'data': {
                        'first_name': serializer.data['first_name'],
                        'token': token,
                    },
                    'message': 'Congratulations, you are registered.',
                }
                return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class HotelLoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            phone = serializer.validated_data.get('phone_number')
            fcm_token = request.data.get('fcm_token')

            try:
                hotel_owner = HotelOwner.objects.get(phone_number=phone)
                if hotel_owner.is_verified:
                    if fcm_token:
                        FCMToken.objects.create(user_id=hotel_owner.id, fcm_token=fcm_token, is_owner=True)

                    token = generate_token(hotel_owner.id)
                    response_data = {
                        'result': True,
                        'data': {
                            'PhoneNumber': phone,
                            'token': token,
                        },
                        'message': 'Congratulations, you are logged in.',
                    }
                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    return Response({'result': False, 'message': 'Owner not verified by admin'}, status=status.HTTP_400_BAD_REQUEST)

            except HotelOwner.DoesNotExist:
                return Response({'result': False, 'message': 'You are not registered.'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)