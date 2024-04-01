from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Customer
from .serializer import RegisterSerializer, LoginSerializer, ProfileSerializer, PopertyListOutSerializer, \
    OrderSummarySerializer, RoomInventoryListSerializer, CombinedSerializer, RatingSerializer, CustomerBookingSerializer
from .utils import generate_token, get_room_inventory, sort_properties_by_price, calculate_available_rooms, get_cancellation_charge_percentage
from hotel.utils import error_response, send_mail, generate_response
from hotel.filters import BookingFilter
from hotel.models import Property, RoomInventory, BookingHistory, OwnerBankingDetail, Ratings, PropertyCancellation
from hotel.paginator import CustomPagination
from hotel.serializer import RoomInventoryOutSerializer, BookingHistorySerializer, RatingsOutSerializer, \
    CancelBookingSerializer
from hotel_app_backend.messages import PHONE_REQUIRED_MESSAGE, PHONE_ALREADY_PRESENT_MESSAGE, \
    REGISTRATION_SUCCESS_MESSAGE, EXCEPTION_MESSAGE, LOGIN_SUCCESS_MESSAGE, NOT_REGISTERED_MESSAGE, \
    PROFILE_MESSAGE, CUSTOMER_NOT_FOUND_MESSAGE, EMAIL_ALREADY_PRESENT_MESSAGE, PROFILE_UPDATE_MESSAGE, \
    PROFILE_ERROR_MESSAGE, ENTITY_ERROR_MESSAGE, PAYMENT_SUCCESS_MESSAGE, DATA_RETRIEVAL_MESSAGE, \
    OBJECT_NOT_FOUND_MESSAGE, ORDER_SUFFICIENT_MESSAGE, BOOKED_INFO_MESSAGE, REQUIREMENT_INFO_MESSAGE, \
    SESSION_INFO_MESSAGE, AVAILABILITY_INFO_MESSAGE, ROOM_NOT_AVAILABLE_MESSAGE, ORDER_ERROR_MESSAGE, \
    REFUND_SUCCESFULL_MESSAGE, REFUND_ERROR_MESSAGE, DIRECT_TRANSFER_ERROR_MESSAGE
from .authentication import JWTAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
# from django.conf import settings
# import razorpay
from rest_framework.generics import RetrieveAPIView, ListAPIView, ListCreateAPIView
from django.http import Http404
from .filters import RoomInventoryFilter
import datetime
from django.db import transaction
from django.db.models import Avg
from django.utils import timezone
from hotel_app_backend.razorpay_utils import razorpay_request
from django.utils.dateparse import parse_date


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
        ratings = self.request.query_params.get('ratings', None)
        hotel_class = self.request.query_params.get('hotel_class', None)
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
        if ratings:
            rating_ranges = [(float(rating.strip()), float(rating.strip()) + 0.5) for rating in ratings.split(',') if rating.replace('.', '', 1).isdigit()]
            properties_with_desired_ratings = Ratings.objects \
                .annotate(average_rating=Avg('ratings')) \
                .filter(average_rating__gte=min(rating_range[0] for rating_range in rating_ranges),
                        average_rating__lte=max(rating_range[1] for rating_range in rating_ranges)) \
                .values_list('property', flat=True).distinct()
            queryset = queryset.filter(id__in=properties_with_desired_ratings)
        if hotel_class:
            queryset = queryset.filter(hotel_class=int(hotel_class))
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
        check_in_date_obj = parse_date(check_in_date)
        check_out_date_obj = parse_date(check_out_date)
        num_nights = (check_out_date_obj - check_in_date_obj).days
        total_price = room.default_price * min(adjusted_availability, int(num_of_rooms)) * num_nights
        gst_rate = 0.12 if total_price <= 7500 else 0.18
        gst_amount = total_price * gst_rate
        final_price = total_price + gst_amount
        booked_info = BOOKED_INFO_MESSAGE.format(total_booked=total_booked)
        session_info = SESSION_INFO_MESSAGE.format(session_rooms_booked=session_rooms_booked)
        availability_info = AVAILABILITY_INFO_MESSAGE.format(adjusted_availability=adjusted_availability)
        requirement_info = REQUIREMENT_INFO_MESSAGE.format(additional_rooms_needed=int(num_of_rooms) - adjusted_availability)
        serializer = self.serializer_class(room, context={"start_date": check_in_date, "end_date": check_out_date})
        return Response({
            'result': True,
            'data': {
                **serializer.data,
                'num_of_rooms': int(num_of_rooms),
                'available_rooms': adjusted_availability,
                'total_price': total_price,
                'gst_rate': gst_rate * 100,
                'gst_amount': gst_amount,
                'final_price': final_price,
            },
            'message': ORDER_SUFFICIENT_MESSAGE if adjusted_availability >= int(num_of_rooms) else f"{availability_info} {booked_info} {session_info} {requirement_info}"
        }, status=status.HTTP_200_OK)


class PayNowView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            with transaction.atomic():
                booking_data = request.data.get('booking_detail', {})
                guest_data = request.data.get('guest_detail', {})

                room_id = booking_data.get('rooms')
                room_instance = RoomInventory.objects.select_for_update().get(id=room_id)
                property_instance = Property.objects.get(id=booking_data.get('property'))

                owner_banking_detail = OwnerBankingDetail.objects.get(hotel_owner=property_instance.owner, status=True)
                account_id = owner_banking_detail.account_id
                amount = float(booking_data.get('amount'))
                currency = 'INR'
                num_of_rooms = booking_data.get('num_of_rooms')
                check_in_date = booking_data.get('check_in_date')
                check_out_date = booking_data.get('check_out_date')
                total_booked, available_rooms, session_rooms_booked = calculate_available_rooms(room_instance, check_in_date, check_out_date, self.request.session)
                adjusted_availability = available_rooms - session_rooms_booked
                if available_rooms < int(num_of_rooms) or adjusted_availability < int(num_of_rooms):
                    return error_response(ROOM_NOT_AVAILABLE_MESSAGE, status.HTTP_400_BAD_REQUEST)
                commission_percent = property_instance.commission_percent
                commission_percent = property_instance.commission_percent
                commission_amount = (amount * commission_percent) / 100
                remaining_amount = amount - commission_amount
                remaining_amount_in_paise = int(remaining_amount * 100)
                on_hold_until_timestamp = self.calculate_on_hold_until(check_in_date)
                session_key = 'room_id_' + str(room_id)
                request.session[session_key] = {
                    'room_id': room_id,
                    'num_of_rooms': num_of_rooms
                }
                request.session.set_expiry(60)
                order = self.create_payment_order(amount, remaining_amount_in_paise, account_id, currency, on_hold_until_timestamp)
                if not order:
                    return error_response("Failed to create payment order", status.HTTP_500_INTERNAL_SERVER_ERROR)
                serializer_data = {
                    'booking_detail': booking_data,
                    'guest_detail': guest_data
                }

                serializer = CombinedSerializer(data=serializer_data, context={'request': request,
                                                                               'property': property_instance,
                                                                               'room': room_instance,
                                                                               'order_id': order['id'],
                                                                               'transfer_id': order['transfers'][0]['id']})
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        'result': True,
                        'data': {'order_id': order['id']},
                        'message': PAYMENT_SUCCESS_MESSAGE
                    }, status=status.HTTP_200_OK)
                else:
                    return error_response(serializer.errors, status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(e)
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)

    def create_payment_order(self, amount, remaining_amount_in_paise, account_id, currency, on_hold_until_timestamp):
        order_data = {
            'amount': amount * 100,
            'currency': currency,
            'transfers': [
                {
                    'account': account_id,
                    'amount': remaining_amount_in_paise,
                    'currency': currency,
                    'on_hold': True,
                    'on_hold_until': on_hold_until_timestamp,
                }
            ]
        }
        # response = requests.post(settings.RAZORPAY_BASE_URL + '/v1/orders', headers=headers, json=order_data)
        response = razorpay_request('/v1/orders', "post", data=order_data)
        if response.status_code == 200:
            return response.json()
        return None

    def calculate_on_hold_until(self, check_in_date_str):
        check_in_date_obj = datetime.datetime.strptime(check_in_date_str, '%Y-%m-%d').date()
        current_date = datetime.datetime.now().date()
        if check_in_date_obj <= current_date:
            on_hold_until_date_obj = check_in_date_obj + datetime.timedelta(days=1)
        else:
            on_hold_until_date_obj = check_in_date_obj
        on_hold_until_datetime_obj = datetime.datetime.combine(on_hold_until_date_obj, datetime.time.max)
        return int(on_hold_until_datetime_obj.timestamp())


class BookingListView(ListAPIView):
    authentication_classes = (JWTAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = BookingHistorySerializer
    pagination_class = CustomPagination
    filterset_class = BookingFilter
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        queryset = BookingHistory.objects.filter(customer=self.request.user, book_status=True, is_cancel=False).order_by('-created_at')
        return queryset


class BookingRetrieveView(RetrieveAPIView):
    authentication_classes = (JWTAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = CustomerBookingSerializer

    def get_queryset(self):
        queryset = BookingHistory.objects.filter(customer=self.request.user, book_status=True).order_by('-created_at')
        return queryset

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            return generate_response(instance, DATA_RETRIEVAL_MESSAGE, status.HTTP_200_OK, self.serializer_class)
        except Http404:
            return error_response(OBJECT_NOT_FOUND_MESSAGE, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


class PropertyRatingView(ListCreateAPIView):
    authentication_classes = (JWTAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = RatingSerializer
    pagination_class = CustomPagination

    def create(self, request, *args, **kwargs):
        try:
            property_id = self.kwargs.get('property_id')
            property_instance = Property.objects.get(id=property_id)
            serializer = self.serializer_class(data=request.data)
            if serializer.is_valid():
                serializer.save(property=property_instance, customer=self.request.user)
            return generate_response(serializer.data, DATA_RETRIEVAL_MESSAGE, status.HTTP_200_OK, self.serializer_class)
        except Property.DoesNotExist:
            return error_response(OBJECT_NOT_FOUND_MESSAGE, status.HTTP_400_BAD_REQUEST)
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        try:
            property_id = self.kwargs.get('property_id')
            ratings = Ratings.objects.filter(property=property_id).order_by('-created_at')
            page = self.paginate_queryset(ratings)
            serializer = RatingsOutSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


class CancelBookingView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            id = self.kwargs.get('id')
            booking = BookingHistory.objects.get(id=id)
            check_in_date = booking.check_in_date.date()

            cancellation_policies = PropertyCancellation.objects.filter(property=booking.property).order_by('cancellation_days')
            owner = OwnerBankingDetail.objects.get(hotel_owner=booking.property.owner, status=True)
            days_before_check_in = (check_in_date - timezone.now().date()).days
            check_in_time = booking.property.check_in_time
            if not cancellation_policies.exists():
                refund_amount = 0
            else:
                cancellation_charge_percentage = get_cancellation_charge_percentage(cancellation_policies, days_before_check_in, check_in_time)
                cancellation_charge_amount = (booking.amount * cancellation_charge_percentage) / 100
                refund_amount = booking.amount - cancellation_charge_amount
            if refund_amount == 0:
                serializer = CancelBookingSerializer(booking, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save(is_cancel=True, cancel_date=timezone.now())
                    response_serializer = BookingHistorySerializer(booking, fields=('id', 'order_id', 'transfer_id', 'payment_id'))
                    return generate_response(response_serializer.data, REFUND_SUCCESFULL_MESSAGE, status.HTTP_200_OK)
                else:
                    return error_response(REFUND_ERROR_MESSAGE, status.HTTP_400_BAD_REQUEST)

            commission_percent = booking.property.commission_percent
            commission_amount = (cancellation_charge_amount * commission_percent) / 100
            transfer_amount = cancellation_charge_amount - commission_amount
            order_response = razorpay_request(f"/v1/transfers/{booking.transfer_id}", "patch", data={"on_hold": 1})
            if order_response.status_code != 200:
                return error_response(ORDER_ERROR_MESSAGE, status.HTTP_400_BAD_REQUEST)
            refund_response = razorpay_request(f"/v1/payments/{booking.payment_id}/refund", "post", data={"amount": refund_amount * 100})
            if refund_response.status_code != 200:
                return error_response(REFUND_ERROR_MESSAGE, status.HTTP_400_BAD_REQUEST)
            if transfer_amount > 0:
                transfer_data = {
                    "amount": transfer_amount * 100,
                    "currency": booking.currency,
                    "account": owner.account_id
                }
                direct_transfer_response = razorpay_request("/v1/transfers", "post", data=transfer_data)
                if direct_transfer_response.status_code != 200:
                    return error_response(DIRECT_TRANSFER_ERROR_MESSAGE, status.HTTP_400_BAD_REQUEST)
            serializer = CancelBookingSerializer(booking, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save(is_cancel=True, cancel_date=timezone.now())
                response_serializer = BookingHistorySerializer(booking, fields=('id', 'order_id', 'transfer_id', 'payment_id'))
                return generate_response(response_serializer.data, REFUND_SUCCESFULL_MESSAGE, status.HTTP_200_OK)
            else:
                return error_response(REFUND_ERROR_MESSAGE, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)
