from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Customer
from .serializer import RegisterSerializer, LoginSerializer, ProfileSerializer
from .utils import generate_token
from hotel.utils import error_response, send_mail
from hotel_app_backend.messages import PHONE_REQUIRED_MESSAGE, PHONE_ALREADY_PRESENT_MESSAGE, \
    REGISTRATION_SUCCESS_MESSAGE, EXCEPTION_MESSAGE, LOGIN_SUCCESS_MESSAGE, NOT_REGISTERED_MESSAGE, \
    PROFILE_MESSAGE, CUSTOMER_NOT_FOUND_MESSAGE, EMAIL_ALREADY_PRESENT_MESSAGE, PROFILE_UPDATE_MESSAGE, \
    PROFILE_ERROR_MESSAGE, ENTITY_ERROR_MESSAGE
from .authentication import JWTAuthentication
from hotel.models import Property
from hotel.serializer import PropertyOutSerializer
from hotel.paginator import CustomPagination
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from .filters import PropertyFilter


class CustomerRegisterView(APIView):
    permission_classes = (permissions.AllowAny, )

    def post(self, request):
        try:
            serializer = RegisterSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            phone_number = serializer.validated_data.get('phone_number')
            if not phone_number:
                return error_response(PHONE_REQUIRED_MESSAGE, status.HTTP_400_BAD_REQUEST)
            if Customer.objects.filter(phone_number=phone_number).exists():
                return error_response(PHONE_ALREADY_PRESENT_MESSAGE, status.HTTP_400_BAD_REQUEST)
            else:
                serializer.save()
                user_id = serializer.instance.id
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
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


class CustomerLoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            phone = serializer.validated_data.get('phone_number')
            device_id = serializer.validated_data.get('device_id')
            fcm_token = serializer.validated_data.get('fcm_token')
            try:
                customer = Customer.objects.get(phone_number=phone)
                if device_id and fcm_token:
                    customer.device_id = device_id
                    customer.fcm_token = fcm_token
                    customer.save()
                else:
                    return error_response(ENTITY_ERROR_MESSAGE, status.HTTP_400_BAD_REQUEST)
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
                return error_response(NOT_REGISTERED_MESSAGE, status.HTTP_400_BAD_REQUEST)
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


class CustomerProfileView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ProfileSerializer

    def get(self, request):

        try:
            serializer = self.serializer_class(request.user)

            response_data = {
                'result': True,
                'data': serializer.data,
                'message': PROFILE_MESSAGE
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except Customer.DoesNotExist:
            return error_response(CUSTOMER_NOT_FOUND_MESSAGE, status.HTTP_404_NOT_FOUND)

        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def patch(self, request):
        try:
            serializer = ProfileSerializer(request.user, data=request.data, partial=True)

            if serializer.is_valid():
                email = serializer.validated_data.get('email', None)
                phone_number = serializer.validated_data.get('phone_number', None)

                if phone_number and Customer.objects.filter(phone_number=phone_number).exists():
                    return error_response(PHONE_ALREADY_PRESENT_MESSAGE, status.HTTP_400_BAD_REQUEST)
                if email:
                    if Customer.objects.filter(email=email).exists():
                        return error_response(EMAIL_ALREADY_PRESENT_MESSAGE, status.HTTP_400_BAD_REQUEST)
                    else:
                        data = {
                            "subject": f'Welcome {request.user.first_name}',
                            "email": email,
                            "template": "welcome_customer.html",
                            "context": {'first_name': request.user.first_name, 'last_name': request.user.last_name}
                        }
                        send_mail(data)
                serializer.save()

                response_data = {
                    'result': True,
                    'data': serializer.data,
                    'message': PROFILE_UPDATE_MESSAGE
                }
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return error_response(PROFILE_ERROR_MESSAGE, status.HTTP_400_BAD_REQUEST)

        except Customer.DoesNotExist:
            return error_response(CUSTOMER_NOT_FOUND_MESSAGE, status.HTTP_404_NOT_FOUND)

        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_500_INTERNAL_SERVER_ERROR)


class HotelRetrieveView(ListAPIView):
    authentication_classes = (JWTAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    queryset = Property.objects.all().order_by('-id')
    serializer_class = PropertyOutSerializer
    pagination_class = CustomPagination
    filterset_class = PropertyFilter
    filter_backends = [DjangoFilterBackend]  
