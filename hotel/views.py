from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Owner, FCMToken
from .serializer import *
from .utils import generate_token
from hotel_app_backend.messages import *
from .authentication import JWTAuthentication

class HotelRegisterView(APIView):
    permission_classes = (permissions.AllowAny, )

    def post(self, request):
        try:
            serializer = RegisterSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            phone_number = serializer.validated_data.get('phone_number')
            fcm_token = request.data.get('fcm_token')

            if not phone_number:
                return Response({'result': False, 'message': PHONE_REQUIRED_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)

            if Owner.objects.filter(phone_number=phone_number).exists():
                return Response({'result': False, 'message': PHONE_ALREADY_PRESENT_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)
             
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
                    'message': REGISTRATION_SUCCESS_MESSAGE
                }
                return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception:
            return Response({'result': False, 'message': EXCEPTION_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)


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
                        'result': True,
                        'data': {
                            'PhoneNumber': phone,
                            'token': token,
                        },
                        'message': LOGIN_SUCCESS_MESSAGE
                    }
                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    return Response({'result': False, 'message': OWNER_NOT_VERIFIED_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)

            except Owner.DoesNotExist:
                return Response({'result': False, 'message': NOT_REGISTERED_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)

        except Exception:
            return Response({'result': False, 'message': EXCEPTION_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)


class OwnerProfileView(APIView):
    authentication_classes = (JWTAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )

    def get(self,request):
        try:
            serializer = OwnerProfileSerializer(request.user)
    
            return Response({"result": True,
                            "data": serializer.data,
                            "message": PROFILE_MESSAGE}, status=status.HTTP_200_OK)
        except Owner.DoesNotExist:
            return Response({'result': False, 'message': OWNER_NOT_FOUND_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'result': False, 'message': EXCEPTION_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)


    def patch(self, request):
        try:
            serializer = OwnerProfileSerializer(request.user, data=request.data, partial=True)
            if serializer.is_valid():

                email = serializer.validated_data.get('email', None)
                phone_number = serializer.validated_data.get('phone_number', None)

                if phone_number and Owner.objects.filter(phone_number=phone_number):
                    return Response({'result': False, 'message': PHONE_ALREADY_PRESENT_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)
                if email and Owner.objects.filter(email=email):
                    return Response({'result': False, 'message': EMAIL_ALREADY_PRESENT_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)

                serializer.save()
                return Response({"result": True,
                                "data": serializer.data,
                                'message': PROFILE_UPDATE_MESSAGE},status=status.HTTP_201_CREATED)
            else:
                return Response({"result": False,
                                "message": PROFILE_ERROR_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)
       
        except Exception:
            return Response({'result': False, 'message': EXCEPTION_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)