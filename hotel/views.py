from django.shortcuts import render
from rest_framework import filters
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status, generics
from django.template.loader import render_to_string
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from .models import Hotel,FCMToken
from .serializer import *
from .utils import generate_token
from .authentication import JWTAuthentication

# Create your views here.
class HotelRegisterView(APIView):
    permission_classes = (permissions.AllowAny, )

    def post(self, request):
        try:
            serializer = RegisterSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            phone_number = serializer.validated_data.get('phone_number')
            fcm_token = request.GET.get('fcm_token')
            print(fcm_token)

            if not phone_number:
                return Response({'result': False, 'message': 'phone number is required for registration.'}, status=status.HTTP_400_BAD_REQUEST)

            if Hotel.objects.filter(phone_number=phone_number).exists():
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
            print(e)
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class HotelLoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            phone = serializer.validated_data.get('phone_number')
            fcm_token = request.GET.get('fcm_token')

            # Check if the customer with the given phone number exists
            try:
                hotel = Hotel.objects.get(phone_number=phone)
                # Customer exists, update the fcm_token
                if fcm_token:
                    FCMToken.objects.create(user_id=hotel.id, fcm_token=fcm_token, is_owner=True)

                # Generate token and return the response
                token = generate_token(hotel.id)
                response_data = {
                    'result': True,
                    'data': {
                        'PhoneNumber': phone,
                        'token': token,
                    },
                    'message': 'Congratulations, you are logged in.',
                }
                return Response(response_data, status=status.HTTP_200_OK)

            except Hotel.DoesNotExist:
                # Customer doesn't exist, return an error response
                return Response({'result': False, 'message': 'You are not registered.'}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(e)
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)