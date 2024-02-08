from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Customer
from .serializer import RegisterSerializer, LoginSerializer, ProfileSerializer, PopertyListOutSerializer
from .utils import generate_token
from hotel.utils import error_response, send_mail
from hotel_app_backend.messages import PHONE_REQUIRED_MESSAGE, PHONE_ALREADY_PRESENT_MESSAGE, \
    REGISTRATION_SUCCESS_MESSAGE, EXCEPTION_MESSAGE, LOGIN_SUCCESS_MESSAGE, NOT_REGISTERED_MESSAGE, \
    PROFILE_MESSAGE, CUSTOMER_NOT_FOUND_MESSAGE, EMAIL_ALREADY_PRESENT_MESSAGE, PROFILE_UPDATE_MESSAGE, \
    PROFILE_ERROR_MESSAGE, ENTITY_ERROR_MESSAGE
from .authentication import JWTAuthentication
from hotel.models import Property, RoomInventory
from hotel.serializer import PropertyOutSerializer
from hotel.paginator import CustomPagination
from rest_framework.generics import ListAPIView
from django_filters.rest_framework import DjangoFilterBackend
from .filters import PropertyFilter
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from rest_framework import status, generics
from django.db.models import Subquery
from django.db.models import Q
from django.http import JsonResponse


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


# class HotelRetrieveView(ListAPIView):
#     authentication_classes = (JWTAuthentication, )
#     permission_classes = (permissions.IsAuthenticated, )
#     queryset = Property.objects.all().order_by('-id')
#     serializer_class = PopertyListOutSerializer
#     pagination_class = CustomPagination
#     filterset_class = PropertyFilter
#     filter_backends = [DjangoFilterBackend]

#     def list(self, request, *args, **kwargs):
#         num_of_rooms = self.request.query_params.get('num_of_rooms')
#         if num_of_rooms:
#             num_of_rooms = int(num_of_rooms)
#             property_list = []
#             for property in self.get_queryset():
#                 rooms = RoomInventory.objects.filter(property=property).order_by('default_price')[:num_of_rooms]
#                 property.room_inventory = rooms
#                 property_list.append(property)
#             page = self.paginate_queryset(property_list)
#             serializer = self.serializer_class(page, many=True, context={'num_of_rooms': num_of_rooms})
#             return self.get_paginated_response(serializer.data)
#         return super().list(request, *args, **kwargs)

class HotelRetrieveView(generics.GenericAPIView):
    authentication_classes = (JWTAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    queryset = Property.objects.all().order_by('-id')
    serializer_class = PopertyListOutSerializer
    pagination_class = CustomPagination
    # filterset_class = PropertyFilter
    filter_backends = [DjangoFilterBackend]

    def get(self, request, *args, **kwargs):
        location_param = self.request.query_params.get('location')
        num_of_rooms = self.request.query_params.get('num_of_rooms')
        nearby_popular_landmark = self.request.query_params.get('nearby_popular_landmark')
        room_type = self.request.query_params.get('room_type')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        num_of_adults = self.request.query_params.get('num_of_adults')
        num_of_children = self.request.query_params.get('num_of_children')
        if location_param is not None or num_of_rooms is not None:
            if location_param is not None:
                longitude, latitude = map(float, location_param.split(','))
                point = Point(longitude, latitude, srid=4326)
                queryset = self.queryset.filter(location__distance_lte=(point, D(m=1000)))

            if num_of_rooms is not None:
                num_of_rooms = int(num_of_rooms)
            if room_type is not None:
                queryset = queryset.filter(room_types__room_type=room_type)
            property_list = []
            for property in queryset:
                rooms = RoomInventory.objects.filter(
                    property=property, is_verified=True
                ).order_by('default_price')

                if min_price or max_price:
                    rooms = rooms.filter(default_price__gte=float(min_price) if min_price else 0,
                                        default_price__lte=float(max_price) if max_price else float('inf'))

                selected_rooms = list(rooms[:num_of_rooms])
                total_adult_capacity = sum(room.adult_capacity for room in selected_rooms)
                total_children_capacity = sum(room.children_capacity for room in selected_rooms)

                additional_rooms_needed = 0
                # Check if additional rooms are needed to meet capacity requirements
                while total_adult_capacity < int(num_of_adults) or total_children_capacity < int(num_of_children):
                    additional_rooms_needed += 1
                    additional_rooms = list(rooms[num_of_rooms:num_of_rooms + additional_rooms_needed])
                    if not additional_rooms:  # Break if no more rooms are available to add
                        break
                    for room in additional_rooms:
                        total_adult_capacity += room.adult_capacity
                        total_children_capacity += room.children_capacity
                        selected_rooms.append(room)

                    if total_adult_capacity >= int(num_of_adults) and total_children_capacity >= int(num_of_children):
                        break  # Stop if requirements are met

                property.room_inventory = selected_rooms
                property_list.append(property)

            # Pagination and serialization
            page = self.paginate_queryset(property_list)
            context = {'request': request, 'num_of_rooms': num_of_rooms}
            serializer = self.serializer_class(page, many=True, context=context)
            return self.get_paginated_response(serializer.data)
        else:
            if nearby_popular_landmark is not None:
                queryset = self.queryset.filter(nearby_popular_landmark=nearby_popular_landmark)
            else:
                queryset = self.get_queryset()
            page = self.paginate_queryset(queryset)
            serializer = self.serializer_class(page, many=True)
            return self.get_paginated_response(serializer.data)