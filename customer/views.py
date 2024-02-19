from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Customer
from .serializer import RegisterSerializer, LoginSerializer, ProfileSerializer, PopertyListOutSerializer
from .utils import generate_token, get_room_inventory, min_default_price
from hotel.utils import error_response, send_mail
from hotel_app_backend.messages import PHONE_REQUIRED_MESSAGE, PHONE_ALREADY_PRESENT_MESSAGE, \
    REGISTRATION_SUCCESS_MESSAGE, EXCEPTION_MESSAGE, LOGIN_SUCCESS_MESSAGE, NOT_REGISTERED_MESSAGE, \
    PROFILE_MESSAGE, CUSTOMER_NOT_FOUND_MESSAGE, EMAIL_ALREADY_PRESENT_MESSAGE, PROFILE_UPDATE_MESSAGE, \
    PROFILE_ERROR_MESSAGE, ENTITY_ERROR_MESSAGE
from .authentication import JWTAuthentication
from hotel.models import Property
from hotel.paginator import CustomPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from rest_framework import status, generics
from django.conf import settings
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


# class HotelRetrieveView(generics.GenericAPIView):
#     authentication_classes = (JWTAuthentication, )
#     permission_classes = (permissions.IsAuthenticated, )
#     queryset = Property.objects.all().order_by('-id')
#     serializer_class = PopertyListOutSerializer
#     pagination_class = CustomPagination
#     # filterset_class = PropertyFilter
#     filter_backends = [DjangoFilterBackend]

#     def get(self, request, *args, **kwargs):
#         location_param = self.request.query_params.get('location')
#         num_of_rooms = self.request.query_params.get('num_of_rooms')
#         nearby_popular_landmark = self.request.query_params.get('nearby_popular_landmark')
#         room_type = self.request.query_params.get('room_type')
#         min_price = self.request.query_params.get('min_price')
#         max_price = self.request.query_params.get('max_price')
#         num_of_adults = self.request.query_params.get('num_of_adults')
#         num_of_children = self.request.query_params.get('num_of_children')
#         if location_param is not None or num_of_rooms is not None:
#             if location_param is not None:
#                 longitude, latitude = map(float, location_param.split(','))
#                 point = Point(longitude, latitude, srid=4326)
#                 queryset = self.queryset.filter(location__distance_lte=(point, D(m=5000)))

#             if num_of_rooms is not None:
#                 num_of_rooms = int(num_of_rooms)
#             if room_type is not None:
#                 queryset = queryset.filter(room_types__room_type=room_type)
#             property_list = []
#             for property in queryset:
#                 rooms = RoomInventory.objects.filter(property=property, is_verified=True).order_by('default_price')
#                 selected_rooms = list(rooms[:num_of_rooms])
#                 total_adult_capacity = sum(room.adult_capacity for room in selected_rooms)
#                 total_children_capacity = sum(room.children_capacity for room in selected_rooms)
#                 total_rooms_for_property = None
#                 additional_rooms_needed = 0
#                 while total_adult_capacity < int(num_of_adults) or total_children_capacity < int(num_of_children):
#                     additional_rooms_needed += 1
#                     total_rooms_for_property = num_of_rooms + additional_rooms_needed
#                     additional_rooms = list(rooms[:total_rooms_for_property])
#                     if not additional_rooms:
#                         break
#                     for room in additional_rooms:
#                         total_adult_capacity += room.adult_capacity
#                         total_children_capacity += room.children_capacity
#                         if room not in selected_rooms:
#                             selected_rooms.append(room)
#                     if total_adult_capacity >= int(num_of_adults) and total_children_capacity >= int(num_of_children):
#                         break
#                 if min_price or max_price:
#                     all_rooms_meet_price_condition = all(
#                         (float(min_price) <= room.default_price <= float(max_price)) if min_price and max_price else True
#                         for room in selected_rooms
#                     )
#                     if not all_rooms_meet_price_condition:
#                         continue
#                 property.room_inventory = selected_rooms
#                 property_list.append(property)

#             page = self.paginate_queryset(property_list)
#             context = {'request': request, 'num_of_rooms': num_of_rooms, 'total_rooms_for_property': total_rooms_for_property}
#             serializer = self.serializer_class(page, many=True, context=context)
#             return self.get_paginated_response(serializer.data)
#         else:
#             if nearby_popular_landmark is not None:
#                 queryset = self.queryset.filter(nearby_popular_landmark=nearby_popular_landmark)
#             else:
#                 queryset = self.get_queryset()
#             page = self.paginate_queryset(queryset)
#             serializer = self.serializer_class(page, many=True)
#             return self.get_paginated_response(serializer.data)


# Number od rooms logic

# if num_of_rooms is not None and num_of_rooms > 0 and is_preferred_property_type is None:
#     room_inventory_instances = list(room_inventory_instances[:num_of_rooms])
# if min_price is not None or max_price is not None:
#     filtered_room_inventories = [
#         room_instance for room_instance in room_inventory_instances
#         if (min_price is None or room_instance.default_price >= float(min_price)) and 
#         (max_price is None or room_instance.default_price <= float(max_price))
#     ]
#     if filtered_room_inventories:
#         include_property = True
#         room_inventory_instances = filtered_room_inventories
# else:
#     include_property = True

# if not is_preferred_property_type and include_property:
#     room_inventory_instances = room_inventory_instances[:1]
# if include_property:
#     property.room_inventory = [RoomInventoryOutSerializer(room_instance).data for room_instance in room_inventory_instances]
#     property_list.append(property)


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
        num_of_rooms = int(self.request.query_params.get('num_of_rooms'))
        property_type = self.request.query_params.get('property_type')
        nearby_popular_landmark = self.request.query_params.get('nearby_popular_landmark')
        room_type = self.request.query_params.get('room_type')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        num_of_adults = self.request.query_params.get('num_of_adults')
        num_of_children = self.request.query_params.get('num_of_children')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        total_guests = (int(num_of_adults) if num_of_adults is not None else 0) + \
                        (int(num_of_children) if num_of_children is not None else 0)
        is_preferred_property_type = False
        queryset = self.get_queryset()

        if nearby_popular_landmark:
            queryset = queryset.filter(nearby_popular_landmark=nearby_popular_landmark)
        if location_param:
            longitude, latitude = map(float, location_param.split(','))
            point = Point(longitude, latitude, srid=4326)
            queryset = queryset.filter(location__distance_lte=(point, D(m=5000)))
        if property_type:
            queryset = queryset.filter(property_type__id=property_type)
        if total_guests > 5:
            queryset = queryset.filter(property_type__id__in = settings.PREFERRED_PROPERTY_TYPES)
            is_preferred_property_type = True

        property_list = []
        for property in queryset:
            property_list = get_room_inventory(property, num_of_rooms, min_price, max_price, 
                                                is_preferred_property_type, property_list, room_type,
                                                start_date, end_date)

        sorted_properties = sorted(property_list, key=min_default_price)
        page = self.paginate_queryset(sorted_properties)
        serializer = self.serializer_class(page, many=True)
        return self.get_paginated_response(serializer.data)


class CustomerSessionView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        if 'room_ids' in request.data:
            room_ids = request.data.get('room_ids')
            for room_id in room_ids:
                request.session['room_id_' + str(room_id)] = room_id
                request.session.set_expiry(60)
            print(request.session.items())
            return JsonResponse({'message': 'Property IDs set in session successfully.'})
        else:
            return JsonResponse({'error': 'Property IDs parameter is missing.'}, status=400)
