from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Customer
from .serializer import RegisterSerializer, LoginSerializer, ProfileSerializer, PopertyListOutSerializer, \
    OrderSummarySerializer, RoomInventoryListSerializer
from .utils import generate_token, get_room_inventory, min_default_price, is_booking_overlapping
from hotel.utils import error_response, send_mail, generate_response
from hotel.models import Property, RoomInventory
from hotel.paginator import CustomPagination
from hotel.serializer import RoomInventoryOutSerializer
from hotel_app_backend.messages import PHONE_REQUIRED_MESSAGE, PHONE_ALREADY_PRESENT_MESSAGE, \
    REGISTRATION_SUCCESS_MESSAGE, EXCEPTION_MESSAGE, LOGIN_SUCCESS_MESSAGE, NOT_REGISTERED_MESSAGE, \
    PROFILE_MESSAGE, CUSTOMER_NOT_FOUND_MESSAGE, EMAIL_ALREADY_PRESENT_MESSAGE, PROFILE_UPDATE_MESSAGE, \
    PROFILE_ERROR_MESSAGE, ENTITY_ERROR_MESSAGE, PAYMENT_ERROR_MESSAGE, ROOM_IDS_MISSING_MESSAGE, \
    PAYMENT_SUCCESS_MESSAGE, DATA_RETRIEVAL_MESSAGE, OBJECT_NOT_FOUND_MESSAGE
from .authentication import JWTAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.conf import settings
from rest_framework.generics import RetrieveAPIView, ListAPIView
from django.http import Http404
from .filters import RoomInventoryFilter
from django.db.models import Sum


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


class PropertyListView(generics.GenericAPIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Property.objects.all().order_by('-id')
    serializer_class = PopertyListOutSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]

    def get(self, request, *args, **kwargs):
        longitude = self.request.query_params.get('longitude')
        latitude = self.request.query_params.get('latitude')
        num_of_rooms = self.request.query_params.get('num_of_rooms')
        property_type = self.request.query_params.get('property_type')
        nearby_popular_landmark = self.request.query_params.get('nearby_popular_landmark')
        room_type = self.request.query_params.get('room_type')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        num_of_adults = self.request.query_params.get('num_of_adults')
        num_of_children = self.request.query_params.get('num_of_children')
        check_in_date = self.request.query_params.get('check_in_date', None)
        check_out_date = self.request.query_params.get('check_out_date', None)
        total_guests = (int(num_of_adults) if num_of_adults is not None else 0) + \
            (int(num_of_children) if num_of_children is not None else 0)
        queryset = self.get_queryset()
        if nearby_popular_landmark:
            queryset = queryset.filter(nearby_popular_landmark=nearby_popular_landmark)
        if latitude and longitude:
            point = Point(float(longitude), float(latitude), srid=4326)
            queryset = queryset.filter(location__distance_lte=(point, D(m=5000)))
        if property_type:
            property_type_ids = [int(id) for id in property_type.split(',') if id.isdigit()]
            queryset = queryset.filter(property_type__id__in=property_type_ids)
        if total_guests > 5:
            queryset = queryset.filter(property_type__id__in=settings.PREFERRED_PROPERTY_TYPES)
        property_list = []
        for property in queryset:
            property_list = get_room_inventory(property,
                                               property_list if property_list else [],
                                               num_of_rooms=int(num_of_rooms) if num_of_rooms else 0,
                                               min_price=int(min_price) if min_price else None,
                                               max_price=int(max_price) if max_price else None,
                                               room_type=room_type if room_type else None,
                                               check_in_date=check_in_date if check_in_date else None,
                                               check_out_date=check_out_date if check_out_date else None,
                                               num_of_adults=int(num_of_adults if num_of_adults else 0),
                                               num_of_children=int(num_of_children if num_of_children else 0),
                                               session=self.request.session)
        sorted_properties = sorted(property_list, key=min_default_price)
        page = self.paginate_queryset(sorted_properties)
        serializer = self.serializer_class(page, many=True)
        return self.get_paginated_response(serializer.data)


class PropertyRetriveView(RetrieveAPIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Property.objects.all().order_by('-id')

    def retrieve(self, request, *args, **kwargs):
        try:
            room_id = self.request.query_params.get('room_id')
            instance = self.get_object()
            if room_id:
                room_instances = RoomInventory.objects.get(id=int(room_id), property=instance)
                instance.room_inventory = RoomInventoryOutSerializer(room_instances).data
            return generate_response(instance, DATA_RETRIEVAL_MESSAGE, status.HTTP_200_OK, PopertyListOutSerializer)
        except Http404:
            return error_response(OBJECT_NOT_FOUND_MESSAGE, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


class RoomInventoryListView(ListAPIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = RoomInventoryListSerializer
    pagination_class = CustomPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RoomInventoryFilter
    queryset = RoomInventory.objects.none()

    def get_queryset(self):
        property_id = self.kwargs.get('property_id')
        num_of_adults = self.request.query_params.get('num_of_adults')
        num_of_children = self.request.query_params.get('num_of_children')
        queryset = RoomInventory.objects.filter(property__id=property_id, is_verified=True, status=True,
                                                adult_capacity__gte=int(num_of_adults if num_of_adults else 0), children_capacity__gte=int(num_of_children if num_of_children else 0)).order_by('default_price')
        room_ids = [int(key.split('_')[-1]) for key in self.request.session.keys() if key.startswith('room_id_')]
        if room_ids:
            queryset = queryset.exclude(id__in=room_ids)
        if not queryset.exists():
            return self.queryset
        return queryset


class RoomRetriveView(RetrieveAPIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    queryset = RoomInventory.objects.all().order_by('-id')

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            return generate_response(instance, DATA_RETRIEVAL_MESSAGE, status.HTTP_200_OK, RoomInventoryOutSerializer)
        except Http404:
            return error_response(OBJECT_NOT_FOUND_MESSAGE, status.HTTP_400_BAD_REQUEST)
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


class OrderSummaryView(ListAPIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = OrderSummarySerializer

    def list(self, request, *args, **kwargs):
        room_ids = self.request.query_params.get('room_ids')
        check_in_date = self.request.query_params.get('check_in_date')
        check_out_date = self.request.query_params.get('check_out_date')
        num_of_rooms = self.request.query_params.get('num_of_rooms')
        room_ids_list = [int(id) for id in room_ids.split(',') if id.isdigit()]
        queryset = RoomInventory.objects.filter(id__in=room_ids_list).order_by('default_price')
        queryset = is_booking_overlapping(queryset, check_in_date, check_out_date, num_of_rooms, room_list=True)
        
        excluded_room_ids = []
        for key in self.request.session.keys():
            if key.startswith('room_id_'):
                session_data = self.request.session[key]
                session_room_id = session_data.get('room_id')
                session_num_of_rooms = session_data.get('num_of_rooms', 0)
                if session_room_id in room_ids_list and session_num_of_rooms > int(num_of_rooms):
                    excluded_room_ids.append(session_room_id)

        if excluded_room_ids:
            queryset = queryset.exclude(id__in=excluded_room_ids)
        
        total_price = queryset.aggregate(total=Sum('default_price'))['total'] or 0
        serializer = self.serializer_class(queryset, many=True)
        response_data = {
            'result': True,
            'data': {
                'rooms': serializer.data,
                'total_price': total_price,
            },
            'message': "Data retrieval successful."  # Assuming DATA_RETRIEVAL_MESSAGE is defined elsewhere
        }
        return Response(response_data, status=status.HTTP_201_CREATED)



class PayNowView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        if 'room_id' in request.data:
            room_id = request.data.get('room_id')
            num_of_rooms = request.data.get('num_of_rooms')
            # rooms_already_in_session = []
            # for room_id in room_ids:
            #     session_key = 'room_id_' + str(room_id)
            #     if session_key in request.session:
            #         rooms_already_in_session.append(room_id)
            # if rooms_already_in_session:
            #     return error_response(PAYMENT_ERROR_MESSAGE, status.HTTP_400_BAD_REQUEST)
            session_key = 'room_id_' + str(room_id)
            request.session[session_key] = {
                    'room_id': room_id,
                    'num_of_rooms': num_of_rooms
            }
            request.session.set_expiry(60)
            print(self.request.session.items())
            return Response({'result': True, 'message': PAYMENT_SUCCESS_MESSAGE}, status=status.HTTP_200_OK)
        else:
            return error_response(ROOM_IDS_MISSING_MESSAGE, status.HTTP_400_BAD_REQUEST)
