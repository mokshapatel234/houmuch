from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Customer
from .serializer import RegisterSerializer, LoginSerializer, ProfileSerializer, PopertyListOutSerializer, \
    OrderSummarySerializer, RoomInventoryListSerializer, CombinedSerializer
from .utils import generate_token, get_room_inventory, sort_properties_by_price, calculate_available_rooms
from hotel.utils import error_response, send_mail, generate_response
from hotel.filters import BookingFilter
from hotel.models import Property, RoomInventory, BookingHistory
from hotel.paginator import CustomPagination
from hotel.serializer import RoomInventoryOutSerializer, BookingHistorySerializer
from hotel_app_backend.messages import PHONE_REQUIRED_MESSAGE, PHONE_ALREADY_PRESENT_MESSAGE, \
    REGISTRATION_SUCCESS_MESSAGE, EXCEPTION_MESSAGE, LOGIN_SUCCESS_MESSAGE, NOT_REGISTERED_MESSAGE, \
    PROFILE_MESSAGE, CUSTOMER_NOT_FOUND_MESSAGE, EMAIL_ALREADY_PRESENT_MESSAGE, PROFILE_UPDATE_MESSAGE, \
    PROFILE_ERROR_MESSAGE, ENTITY_ERROR_MESSAGE, PAYMENT_SUCCESS_MESSAGE, \
    DATA_RETRIEVAL_MESSAGE, OBJECT_NOT_FOUND_MESSAGE, \
    ORDER_SUFFICIENT_MESSAGE, BOOKED_INFO_MESSAGE, REQUIREMENT_INFO_MESSAGE, \
    SESSION_INFO_MESSAGE, AVAILABILITY_INFO_MESSAGE
from .authentication import JWTAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.conf import settings
import razorpay
from rest_framework.generics import RetrieveAPIView, ListAPIView
from django.http import Http404
from .filters import RoomInventoryFilter


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
    queryset = Property.objects.filter(is_verified=True).order_by('-id')
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
        high_to_low = self.request.query_params.get('high_to_low', False)
        # total_guests = (int(num_of_adults) if num_of_adults is not None else 0) + \
        #     (int(num_of_children) if num_of_children is not None else 0)
        queryset = self.get_queryset()
        if nearby_popular_landmark:
            queryset = queryset.filter(nearby_popular_landmark=nearby_popular_landmark)
        if latitude and longitude:
            point = Point(float(longitude), float(latitude), srid=4326)
            queryset = queryset.filter(location__distance_lte=(point, D(m=5000)))
        if property_type:
            property_type_ids = [int(id) for id in property_type.split(',') if id.isdigit()]
            queryset = queryset.filter(property_type__id__in=property_type_ids)
        # if total_guests > 5:
        #     queryset = queryset.filter(property_type__id__in=settings.PREFERRED_PROPERTY_TYPES)
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
                                               high_to_low=high_to_low,
                                               session=self.request.session)
        sorted_properties = sorted(property_list, key=lambda x: sort_properties_by_price(x, high_to_low=high_to_low))
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
        except Exception:
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
        self.adjusted_availability = {}
        property_id = self.kwargs.get('property_id')
        num_of_adults = self.request.query_params.get('num_of_adults')
        num_of_children = self.request.query_params.get('num_of_children')
        queryset = RoomInventory.objects.filter(property__id=property_id, is_verified=True, status=True,
                                                adult_capacity__gte=int(num_of_adults if num_of_adults else 0), children_capacity__gte=int(num_of_children if num_of_children else 0)).order_by('default_price')
        return queryset if queryset.exists() else self.queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        adjusted_availability = getattr(request, 'adjusted_availability', {})
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, context={'request': request, 'adjusted_availability': adjusted_availability})
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)


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
        room_id = self.request.query_params.get('room_id')
        check_in_date = self.request.query_params.get('check_in_date')
        check_out_date = self.request.query_params.get('check_out_date')
        num_of_rooms = self.request.query_params.get('num_of_rooms')
        room = RoomInventory.objects.get(id=room_id)
        total_booked, available_rooms, session_rooms_booked = calculate_available_rooms(room, check_in_date, check_out_date, self.request.session)
        adjusted_availability = available_rooms - session_rooms_booked
        total_price = room.default_price * min(adjusted_availability, int(num_of_rooms))
        booked_info = BOOKED_INFO_MESSAGE.format(total_booked=total_booked)
        session_info = SESSION_INFO_MESSAGE.format(session_rooms_booked=session_rooms_booked)
        availability_info = AVAILABILITY_INFO_MESSAGE.format(adjusted_availability=adjusted_availability)
        requirement_info = REQUIREMENT_INFO_MESSAGE.format(additional_rooms_needed=int(num_of_rooms) - adjusted_availability)
        serializer = self.serializer_class(room)
        return Response({
            'result': True,
            'data': {
                **serializer.data,
                'available_rooms': adjusted_availability,
                'total_price': total_price,
            },
            'message': ORDER_SUFFICIENT_MESSAGE if adjusted_availability >= int(num_of_rooms) else f"{availability_info} {booked_info} {session_info} {requirement_info}"
        }, status=status.HTTP_200_OK)


class PayNowView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            room_id = request.data.get('room_id')
            room = RoomInventory.objects.get(id=room_id)
            property_id = request.data.get('property_id')
            property_instance = Property.objects.get(id=property_id)
            amount = request.data.get('amount')
            customer_id = request.user.id
            customer_instance = Customer.objects.get(id=customer_id)
            currency = 'INR'
            check_in_date = request.data.get('check_in_date')
            check_out_date = request.data.get('check_out_date')
            num_of_rooms = request.data.get('num_of_rooms')
            total_booked, available_rooms, session_rooms_booked = calculate_available_rooms(room, check_in_date, check_out_date, self.request.session)
            adjusted_availability = available_rooms - session_rooms_booked
            if available_rooms < int(num_of_rooms) or adjusted_availability < int(num_of_rooms):
                return error_response("rooms are not available as per you requirements.", status.HTTP_400_BAD_REQUEST)
            razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))
            order = razorpay_client.order.create({'amount': amount * 100, 'currency': currency})
            request.data['customer_id'] = customer_instance.id
            serializer = CombinedSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save(property=property_instance, order_id=order['id'], customer=customer_instance, book_status=True, rooms=room, currency=currency)
                session_key = 'room_id_' + str(room_id)
                request.session[session_key] = {
                    'room_id': room_id,
                    'num_of_rooms': request.data.get('num_of_rooms')
                }
                request.session.set_expiry(60)
                response_data = {
                    'result': True,
                    'data': {
                        'order_id': order['id'],
                    },
                    'message': PAYMENT_SUCCESS_MESSAGE
                }
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return error_response(str(e), status.HTTP_500_INTERNAL_SERVER_ERROR)


class BookingListView(ListAPIView):
    authentication_classes = (JWTAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = BookingHistorySerializer
    pagination_class = CustomPagination
    filterset_class = BookingFilter
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        queryset = BookingHistory.objects.filter(customer=self.request.user, book_status=True).order_by('-created_at')
        return queryset
