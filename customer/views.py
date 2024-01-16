from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Customer
from hotel.models import FCMToken
from .serializer import *
from .utils import generate_token
from hotel_app_backend.messages import *
from .authentication import JWTAuthentication 

class CustomerRegisterView(APIView):
    permission_classes = (permissions.AllowAny, )

    def post(self, request):
        try:
            serializer = RegisterSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            phone_number = serializer.validated_data.get('phone_number')
            fcm_token = request.data.get('fcm_token')

            if not phone_number:
                return Response({'result': False, 'message': PHONE_REQUIRED_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)

            if Customer.objects.filter(phone_number=phone_number).exists():
                return Response({'result': False, 'message': PHONE_ALREADY_PRESENT_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)

            else:
                serializer.save()
                user_id = serializer.instance.id

                if fcm_token:
                    FCMToken.objects.create(user_id=user_id, fcm_token=fcm_token)

                token = generate_token(user_id)

                response_data = {
                    'result': True,
                    'data': {
                        **serializer.data,
                        'token': token,
                    },
                    'message': REGISTRATION_SUCCESS_MESSAGE
                }
                return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception:
            return Response({'result': False, 'message': EXCEPTION_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)


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
                print(customer)
                if fcm_token:
                    FCMToken.objects.create(user_id=customer.id, fcm_token=fcm_token)

                    token = generate_token(customer.id)
                    customer_data = serializer.to_representation(customer)
                    response_data = {
                        'result': True,
                        'data': {
                            **customer_data,
                            'token': token,
                        },
                        'message': LOGIN_SUCCESS_MESSAGE
                    }
                    return Response(response_data, status=status.HTTP_200_OK)

            except Customer.DoesNotExist:
                return Response({'result': False, 'message': NOT_REGISTERED_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)

        except Exception:
            return Response({'result': False, 'message': EXCEPTION_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)


class CustomerProfileView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ProfileSerializer

    def get(self, request):

        try:
            serializer = ProfileSerializer(request.user)

            response_data = {
                'result': True,
                'data': serializer.data,
                'message': PROFILE_MESSAGE
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except Customer.DoesNotExist:
            return Response({'result': False, 'message': CUSTOMER_NOT_FOUND_MESSAGE}, status=status.HTTP_404_NOT_FOUND)

        except Exception:
            return Response({'result': False, 'message': EXCEPTION_MESSAGE}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def patch(self, request):
        try:
            serializer = ProfileSerializer(request.user, data=request.data, partial=True)

            if serializer.is_valid():
                email = serializer.validated_data.get('email', None)
                phone_number = serializer.validated_data.get('phone_number', None)

                if email and Customer.objects.filter(email=email).exists():
                    return Response({'result': False, 'message': EMAIL_ALREADY_PRESENT_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)

                if phone_number and Customer.objects.filter(phone_number=phone_number).exists():
                    return Response({'result': False, 'message': PHONE_ALREADY_PRESENT_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)

                serializer.save()

                response_data = {
                    'result': True,
                    'data': serializer.data,
                    'message': PROFILE_UPDATE_MESSAGE
                }
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response({'result': False, 'message': PROFILE_ERROR_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)

        except Customer.DoesNotExist:
            return Response({'result': False, 'message': CUSTOMER_NOT_FOUND_MESSAGE}, status=status.HTTP_404_NOT_FOUND)

        except Exception:
            return Response({'result': False, 'message': EXCEPTION_MESSAGE}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)