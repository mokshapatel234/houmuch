from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from .models import Owner, PropertyType, RoomType, BedType, \
    BathroomType, RoomFeature, CommonAmenities, Property, OTP, \
    RoomInventory, RoomImage, Category, PropertyImage, Ratings, UpdateInventoryPeriod, \
    PropertyCancellation, BookingHistory, Product, OwnerBankingDetail, UpdateType, \
    SubscriptionPlan, SubscriptionTransaction, CancellationReason
from .serializer import RegisterSerializer, LoginSerializer, OwnerProfileSerializer, \
    PropertySerializer, PropertyOutSerializer, PropertyTypeSerializer, RoomTypeSerializer, \
    BedTypeSerializer, BathroomTypeSerializer, RoomFeatureSerializer, CommonAmenitiesSerializer, \
    OTPVerificationSerializer, RoomInventorySerializer, RoomInventoryOutSerializer, UpdateInventoryPeriodSerializer, \
    CategorySerializer, PropertyImageSerializer, BookingHistorySerializer, HotelOwnerBankingSerializer, BookingRetrieveSerializer, \
    PatchRequestSerializer, AccountSerializer, SubscriptionPlanSerializer, SubscriptionSerializer, UpdateTypeSerializer, \
    SubscriptionOutSerializer, RatingsOutSerializer, CancellationReasonSerializer, TransactionSerializer, CancelBookingSerializer
from .utils import generate_token, model_name_to_snake_case, generate_response, generate_otp, send_mail, get_days_before_check_in, \
    error_response, deletion_success_response, remove_cache, cache_response, set_cache, check_plan_expiry, update_period, find_month_year
from hotel_app_backend.messages import PHONE_REQUIRED_MESSAGE, PHONE_ALREADY_PRESENT_MESSAGE, \
    REGISTRATION_SUCCESS_MESSAGE, EXCEPTION_MESSAGE, LOGIN_SUCCESS_MESSAGE, \
    NOT_REGISTERED_MESSAGE, OWNER_NOT_FOUND_MESSAGE, PROFILE_MESSAGE, PROFILE_UPDATE_MESSAGE, \
    PROFILE_ERROR_MESSAGE, DATA_RETRIEVAL_MESSAGE, DATA_CREATE_MESSAGE, DATA_UPDATE_MESSAGE, \
    EMAIL_ALREADY_PRESENT_MESSAGE, OTP_VERIFICATION_SUCCESS_MESSAGE, OTP_VERIFICATION_INVALID_MESSAGE, \
    INVALID_INPUT_MESSAGE, OBJECT_NOT_FOUND_MESSAGE, DATA_DELETE_MESSAGE, SENT_OTP_MESSAGE, PLAN_EXPIRY_MESSAGE, \
    ACCOUNT_ERROR_MESSAGE, CREATE_PRODUCT_FAIL_MESSAGE, CANCELLATION_LIMIT_MESSAGE, \
    ACCOUNT_PRODUCT_UPDATION_FAIL_MESSAGE, ACCOUNT_DETAIL_UPDATE_MESSAGE, BANKING_DETAIL_NOT_EXIST_MESSAGE, \
    PRODUCT_AND_BANK_DETAIL_SUCESS_MESSAGE, REFUND_SUCCESFULL_MESSAGE, REFUND_ERROR_MESSAGE, ORDER_ERROR_MESSAGE, \
    ADD_ROOM_LIMIT_MESSAGE
from hotel_app_backend.razorpay_utils import razorpay_request
from .authentication import JWTAuthentication
from rest_framework.generics import ListAPIView, RetrieveAPIView
from .paginator import CustomPagination
from django.contrib.gis.geos import Point
from django.http import Http404
from hotel_app_backend.utils import delete_image_from_s3, razorpay_client
from django.contrib.auth.models import User
from .filters import RoomInventoryFilter, BookingFilter, TransactionFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.conf import settings
from django.shortcuts import get_object_or_404
import hashlib
import hmac
import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from collections import defaultdict
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now
from dateutil.relativedelta import relativedelta
from django.db.models import F, Func
import calendar
from django.db.models import Sum


class HotelRegisterView(APIView):
    permission_classes = (permissions.AllowAny, )

    def post(self, request):
        try:
            serializer = RegisterSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            phone_number = serializer.validated_data.get('phone_number')
            email = serializer.validated_data.get('email', None)
            if not phone_number:
                return error_response(PHONE_REQUIRED_MESSAGE, status.HTTP_400_BAD_REQUEST)
            if Owner.objects.filter(phone_number=phone_number).exists():
                return error_response(PHONE_ALREADY_PRESENT_MESSAGE, status.HTTP_400_BAD_REQUEST)
            else:
                user = serializer.save()
                if email:
                    otp = generate_otp()
                    OTP.objects.create(user=user, otp=otp)
                    data = {
                        "subject": 'OTP Verification',
                        "email": email,
                        "template": "otp.html",
                        "context": {'otp': otp}
                    }
                    send_mail(data)
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


class HotelLoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            phone = serializer.validated_data.get('phone_number')
            fcm_token = request.data.get('fcm_token')
            hotel_owner = Owner.objects.get(phone_number=phone)
            hotel_owner.fcm_token = fcm_token
            hotel_owner.save()
            token = generate_token(hotel_owner.id)
            owner_data = serializer.to_representation(hotel_owner)
            response_data = {
                'result': True,
                'data': {
                    **owner_data,
                    'token': token,
                },
                'message': LOGIN_SUCCESS_MESSAGE
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except Owner.DoesNotExist:
            return error_response(NOT_REGISTERED_MESSAGE, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


class OwnerProfileView(APIView):
    authentication_classes = (JWTAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request):
        try:
            serializer = OwnerProfileSerializer(request.user)
            property = Property.objects.filter(owner=request.user)
            images = PropertyImage.objects.filter(property=property.first())
            image_serializer = PropertyImageSerializer(images, many=True)
            subscription_plan = SubscriptionTransaction.objects.filter(owner=self.request.user, payment_status=True).order_by('-created_at').first()
            is_plan_purchased = False
            if subscription_plan:
                is_plan_purchased = not check_plan_expiry(subscription_plan)
            response_data = {
                'result': True,
                'data': {
                    **serializer.data,
                    "is_property_added": True if property.count() >= 1 else False,
                    "property_count": property.count() if property.count() >= 1 else 0,
                    "images": image_serializer.data,
                    "is_plan_purchased": is_plan_purchased
                },
                'message': PROFILE_MESSAGE,
            }
            return Response(response_data, status=status.HTTP_200_OK)
        except Owner.DoesNotExist:
            return error_response(OWNER_NOT_FOUND_MESSAGE, status.HTTP_400_BAD_REQUEST)
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        try:
            serializer = OwnerProfileSerializer(request.user, data=request.data, partial=True)
            if serializer.is_valid():
                email = serializer.validated_data.get('email', None)
                phone_number = serializer.validated_data.get('phone_number', None)
                if phone_number and Owner.objects.filter(phone_number=phone_number):
                    return error_response(PHONE_ALREADY_PRESENT_MESSAGE, status.HTTP_400_BAD_REQUEST)
                if email:
                    if Owner.objects.filter(email=email):
                        return error_response(EMAIL_ALREADY_PRESENT_MESSAGE, status.HTTP_400_BAD_REQUEST)
                    else:
                        otp = generate_otp()
                        OTP.objects.create(user=request.user, otp=otp)
                        # Send OTP email
                        data = {
                            "subject": 'OTP Verification',
                            "email": email,
                            "template": "otp.html",
                            "context": {'otp': otp}
                        }
                        send_mail(data)

                serializer.save()
                response_data = {
                    'result': True,
                    'data': serializer.data,
                    'message': PROFILE_UPDATE_MESSAGE,
                }
                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                return error_response(PROFILE_ERROR_MESSAGE, status.HTTP_400_BAD_REQUEST)
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


class OTPVerificationView(APIView):
    authentication_classes = (JWTAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )

    def get(self, request):
        try:
            user = request.user
            if user.email:
                otp = generate_otp()
                OTP.objects.create(user=request.user, otp=otp)
                data = {
                    "subject": 'OTP Verification',
                    "email": user.email,
                    "template": "otp.html",
                    "context": {'otp': otp}
                }
                send_mail(data)
                return Response({'result': True, 'message': SENT_OTP_MESSAGE}, status=status.HTTP_200_OK)
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        try:
            serializer = OTPVerificationSerializer(data=request.data)
            if serializer.is_valid():
                user = request.user
                otp_value = serializer.validated_data.get('otp')
                latest_otp = OTP.objects.filter(user=user).order_by('-created_at').first()
                if latest_otp and latest_otp.otp == otp_value:
                    user.is_email_verified = True
                    user.save()
                    OTP.objects.filter(user=user).delete()
                    return Response({'result': True, 'message': OTP_VERIFICATION_SUCCESS_MESSAGE}, status=status.HTTP_200_OK)
                else:
                    return error_response(OTP_VERIFICATION_INVALID_MESSAGE, status.HTTP_400_BAD_REQUEST)
            else:
                return error_response(INVALID_INPUT_MESSAGE, status.HTTP_400_BAD_REQUEST)
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


class CategoryRetrieveView(ListAPIView):
    permission_classes = (permissions.AllowAny,)
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


    def list(self, request, *args, **kwargs):
        try:
            serializer = super().list(request, *args, **kwargs)
            response_data = {
                'result': True,
                'data': serializer.data,
                'message': DATA_RETRIEVAL_MESSAGE,
            }
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


class MasterRetrieveView(ListAPIView):
    permission_classes = (permissions.AllowAny, )

    def list(self, request, *args, **kwargs):
        try:
            # cache_response("master_list", request.user)
            models_and_serializers = {
                Category: CategorySerializer,
                PropertyType: PropertyTypeSerializer,
                RoomType: RoomTypeSerializer,
                BedType: BedTypeSerializer,
                BathroomType: BathroomTypeSerializer,
                RoomFeature: RoomFeatureSerializer,
                CommonAmenities: CommonAmenitiesSerializer,
                CancellationReason: CancellationReasonSerializer,
                UpdateType: UpdateTypeSerializer
            }
            data = {}
            for model, serializer_class in models_and_serializers.items():
                queryset = model.objects.all()
                serializer = serializer_class(queryset, many=True)
                model_name = model_name_to_snake_case(model.__name__)
                data[model_name] = serializer.data
                response_data = {
                    'result': True,
                    'data': data,
                    'message': DATA_RETRIEVAL_MESSAGE,
                }
                # set_cache("master_list", request.user, response_data)
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            print(e)
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


class PropertyViewSet(ModelViewSet):
    authentication_classes = (JWTAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = PropertySerializer
    queryset = Property.objects.all().order_by('-id')
    pagination_class = CustomPagination

    def create(self, request):
        try:
            location_data = request.data.pop('location', None)
            room_types_data = request.data.get('room_types', None)
            images = request.data.pop('images', None)
            cancellation_data_list = request.data.pop('cancellation_data', None)
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save(owner=self.request.user)
            if location_data:
                instance.location = Point(location_data['coordinates'])
                instance.save()
            if room_types_data:
                instance.room_types.set(room_types_data)
            if images:
                PropertyImage.objects.bulk_create([
                    PropertyImage(property=instance, image=image) for image in images
                ])

            if cancellation_data_list:
                PropertyCancellation.objects.bulk_create([
                    PropertyCancellation(
                        property=instance,
                        cancellation_days=cancellation_data['cancellation_days'],
                        cancellation_percents=cancellation_data['cancellation_percents']
                    ) for cancellation_data in cancellation_data_list
                ])
            admin_email = User.objects.filter(is_superuser=True).first().email
            data = {
                "subject": 'Property Verification',
                "email": admin_email,
                "template": "property_verify.html",
                "context": {
                    'property_name': instance.owner.hotel_name,
                    'parent_hotel_group': instance.parent_hotel_group,
                    'address': instance.owner.address,
                    'property_id': instance.id,
                    'backend_url': settings.BACKEND_URL
                }
            }
            send_mail(data)
            return generate_response(instance, DATA_CREATE_MESSAGE, status.HTTP_200_OK, PropertyOutSerializer)
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            return generate_response(instance, DATA_RETRIEVAL_MESSAGE, status.HTTP_200_OK, PropertyOutSerializer)
        except Http404:
            return error_response(OBJECT_NOT_FOUND_MESSAGE, status.HTTP_400_BAD_REQUEST)
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            location_data = request.data.pop('location', None)
            room_types_data = request.data.get('room_types', None)
            removed_images = request.data.pop('removed_images', None)
            images = request.data.pop('images', None)
            cancellation_data_list = request.data.pop('cancellation_data', None)
            removed_cancellation_poilcies = request.data.pop('removed_cancellation_poilcies', None)
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            updated_instance = serializer.save()
            if location_data:
                updated_instance.location = Point(location_data['coordinates'])
                updated_instance.save()
            if room_types_data:
                updated_instance.room_types.set(room_types_data)
            if images:
                stored_images = PropertyImage.objects.filter(property=instance)
                stored_images.exclude(image__in=images)
                new_images = [
                    PropertyImage(property=instance, image=image_url)
                    for image_url in set(images) - set(stored_images.values_list('image', flat=True))
                ]
                PropertyImage.objects.bulk_create(new_images)
            if cancellation_data_list:
                for cancellation_data in cancellation_data_list:
                    PropertyCancellation.objects.update_or_create(
                        property=instance,
                        cancellation_days=cancellation_data['cancellation_days'],
                        defaults={'cancellation_percents': cancellation_data['cancellation_percents']}
                    )
            if removed_cancellation_poilcies:
                for removed_cancellation_poilcy in removed_cancellation_poilcies:
                    PropertyCancellation.objects.filter(property=instance,
                                                        cancellation_days=removed_cancellation_poilcy['cancellation_days'],
                                                        cancellation_percents=removed_cancellation_poilcy['cancellation_percents']).delete()
            if removed_images:
                for removed_image_url in removed_images:
                    delete_image_from_s3(removed_image_url)
                    PropertyImage.objects.filter(property=instance, image=removed_image_url).delete()
            return generate_response(updated_instance, DATA_UPDATE_MESSAGE, status.HTTP_200_OK, PropertyOutSerializer)
        except Http404:
            return error_response(OBJECT_NOT_FOUND_MESSAGE, status.HTTP_400_BAD_REQUEST)
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        try:
            queryset = Property.objects.filter(owner=request.user).order_by('-id')
            page = self.paginate_queryset(queryset)
            serializer = PropertyOutSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


class RoomInventoryViewSet(ModelViewSet):
    authentication_classes = (JWTAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = RoomInventorySerializer
    queryset = RoomInventory.objects.all().order_by('-id')
    pagination_class = CustomPagination
    filterset_class = RoomInventoryFilter
    filter_backends = [DjangoFilterBackend]

    def create(self, request):
        try:
            property_id = request.GET.get('property_id')
            bed_type = request.data.get('bed_type', None)
            room_features = request.data.get('room_features', None)
            common_amenities = request.data.get('common_amenities', None)
            updated_period_data = request.data.pop('updated_period', None)
            images = request.data.pop('images', None)
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            property_instance = Property.objects.get(id=property_id)
            number_of_rooms_limit = property_instance.number_of_rooms
            total_rooms = RoomInventory.objects.filter(property=property_instance).aggregate(total_rooms=Sum('num_of_rooms'))['total_rooms'] or 0
            number_of_rooms_limit = property_instance.number_of_rooms
            if total_rooms >= number_of_rooms_limit:
                return error_response(ADD_ROOM_LIMIT_MESSAGE, status.HTTP_400_BAD_REQUEST)
            instance = serializer.save(property=property_instance)
            image_instances = []
            if updated_period_data:
                update_period(updated_period_data, instance)
            if room_features:
                instance.room_features.set(room_features)
            if common_amenities:
                instance.common_amenities.set(common_amenities)
            if bed_type:
                instance.bed_type.set(bed_type)
            if images:
                for image in images:
                    image_instances.append(RoomImage(room=instance, image=image))

            if image_instances:
                RoomImage.objects.bulk_create(image_instances)
            admin_email = User.objects.filter(is_superuser=True).first().email
            data = {
                "subject": 'Room Verification',
                "email": admin_email,
                "template": "room_verify.html",
                "context": {
                    'room_name': instance.room_name,
                    'property_name': property_instance.owner.hotel_name,
                    'floor': instance.floor,
                    'address': property_instance.owner.address,
                    'room_id': instance.id,
                    'backend_url': settings.BACKEND_URL
                }
            }
            send_mail(data)
            # remove_cache("room_inventory_list", request.user)
            return generate_response(instance, DATA_CREATE_MESSAGE, status.HTTP_200_OK, RoomInventoryOutSerializer)
        except Exception as e:
            print(e)
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            today = now().date()
            start_date = today.replace(day=1)
            end_date = start_date + relativedelta(months=+6)
            updated_inventory = UpdateInventoryPeriod.objects.filter(
                room_inventory=instance,
                date__range=(start_date, end_date),
                is_deleted=False,
            ).annotate(
                month=Func(F('date'), function='EXTRACT', template="%(function)s(MONTH from %(expressions)s)"),
                year=Func(F('date'), function='EXTRACT', template="%(function)s(YEAR from %(expressions)s)"),
            ).order_by('year', 'month', 'type')
            grouped_data = []
            for item in updated_inventory:
                month_year = f"{calendar.month_name[int(item.month)]} {int(item.year)}"
                month_year_group = find_month_year(month_year, grouped_data)
                if not month_year_group:
                    month_year_group = {'month_year': month_year, 'types': defaultdict(list)}
                    grouped_data.append(month_year_group)
                serialized_item = UpdateInventoryPeriodSerializer(item).data
                month_year_group['types'][item.type.type].append(serialized_item)
            for group in grouped_data:
                group['types'] = dict(group['types'])
            response_data = {
                'room_inventory': RoomInventoryOutSerializer(instance).data,
                'updated_inventory': grouped_data
            }
            return generate_response(response_data, DATA_RETRIEVAL_MESSAGE, status.HTTP_200_OK)
        except Http404:
            return error_response(OBJECT_NOT_FOUND_MESSAGE, status.HTTP_400_BAD_REQUEST)
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        try:
            # cache_response("room_inventory_list", request.user)
            queryset = self.filter_queryset(RoomInventory.objects.filter(property__owner=request.user))
            page = self.paginate_queryset(queryset)
            today = now().date()
            start_date = today.replace(day=1)
            end_date = start_date + relativedelta(months=+6)

            def get_updated_inventory(room_inventory):
                updated_inventory = UpdateInventoryPeriod.objects.filter(
                    room_inventory=room_inventory,
                    date__range=(start_date, end_date),
                    is_deleted=False,
                ).annotate(
                    month=Func(F('date'), function='EXTRACT', template="%(function)s(MONTH from %(expressions)s)"),
                    year=Func(F('date'), function='EXTRACT', template="%(function)s(YEAR from %(expressions)s)"),
                ).order_by('year', 'month', 'type')

                grouped_data = []
                for item in updated_inventory:
                    month_year = f"{calendar.month_name[int(item.month)]} {int(item.year)}"
                    month_year_group = next((g for g in grouped_data if g['month_year'] == month_year), None)
                    if not month_year_group:
                        month_year_group = {'month_year': month_year, 'types': defaultdict(list)}
                        grouped_data.append(month_year_group)
                    serialized_item = UpdateInventoryPeriodSerializer(item).data
                    month_year_group['types'][item.type.type].append(serialized_item)

                for group in grouped_data:
                    group['types'] = dict(group['types'])
                return grouped_data

            # Modify each RoomInventory in the page with its updated inventory
            serialized_data = []
            for room_inventory in page:
                inventory_data = RoomInventoryOutSerializer(room_inventory).data
                updated_inventory = get_updated_inventory(room_inventory)
                inventory_data['updated_inventory'] = updated_inventory
                serialized_data.append(inventory_data)

            return self.get_paginated_response(serialized_data)
            # set_cache("room_inventory_list", request.user, serialized_data)
            # return response_data
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            room_features = request.data.get('room_features', None)
            bed_type = request.data.get('bed_type', None)
            common_amenities = request.data.get('common_amenities', None)
            updated_period_data = request.data.pop('updated_period', None)
            images = request.data.pop('images', None)
            removed_images = request.data.pop('removed_images', None)
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            updated_instance = serializer.save()
            if updated_period_data:
                update_period(updated_period_data, instance)
            if room_features:
                updated_instance.room_features.set(room_features)
            if common_amenities:
                updated_instance.common_amenities.set(common_amenities)
            if bed_type:
                instance.bed_type.set(bed_type)
            if images:
                stored_images = RoomImage.objects.filter(room=instance)
                stored_images.exclude(image__in=images)
                new_images = [
                    RoomImage(room=instance, image=image_url)
                    for image_url in set(images) - set(stored_images.values_list('image', flat=True))
                ]
                RoomImage.objects.bulk_create(new_images)
            if removed_images:
                for removed_image_url in removed_images:
                    delete_image_from_s3(removed_image_url)
                    RoomImage.objects.filter(room=instance, image=removed_image_url).delete()
            # remove_cache("room_inventory_list", request.user)
            return generate_response(updated_instance, DATA_CREATE_MESSAGE, status.HTTP_200_OK, RoomInventoryOutSerializer)
        except Http404:
            return error_response(OBJECT_NOT_FOUND_MESSAGE, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.common_amenities.clear()
            instance.room_features.clear()
            RoomInventory.objects.filter(pk=instance.pk).delete()
            return deletion_success_response(DATA_DELETE_MESSAGE, status.HTTP_200_OK)
        except Http404:
            return error_response(OBJECT_NOT_FOUND_MESSAGE, status.HTTP_400_BAD_REQUEST)
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


class AccountCreateApi(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            existing_account = OwnerBankingDetail.objects.filter(hotel_owner=request.user, status=True).first()
            if existing_account:
                return error_response(ACCOUNT_ERROR_MESSAGE, status.HTTP_400_BAD_REQUEST)
            user = Owner.objects.get(id=request.user.id)

            # endpoint = "/v2/accounts"
            # url = settings.RAZORPAY_BASE_URL + endpoint

            request.data['type'] = 'route'
            request.data['email'] = user.email
            request.data['phone'] = user.phone_number

            serializer = HotelOwnerBankingSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            settlements_data = request.data.pop('settlements', {})
            tnc_accepted = request.data.pop('tnc_accepted', False)

            response = razorpay_request("/v2/accounts", "post", data=request.data)
            print(response.json(), "ACCOUNT")
            # response = requests.post(url, json=request.data, headers=headers)
            if response.status_code == 200:
                account_data = response.json()
                instance = serializer.save(
                    hotel_owner=request.user,
                    status=True,
                    account_id=account_data.get('id', ''),
                    type='route'
                )

                product_data = {
                    "product_name": "route"
                }

                # endpoint = f"/v2/accounts/{account_data.get('id', '')}/products"
                # url = settings.RAZORPAY_BASE_URL + endpoint
                # response = requests.post(url, json=product_data, headers=headers)
                response = razorpay_request(f"/v2/accounts/{account_data.get('id', '')}/products", "post", data=product_data)
                print(response.json())
                if response.status_code == 200 and instance is not None:
                    product_data = response.json()
                    product_id = product_data.get("id")
                    product = Product(product_id=product_id)
                    product.owner_banking = instance
                    product.save()

                    # endpoint = f"/v2/accounts/{account_data.get('id', '')}/products/{product_id}/"
                    # url = settings.RAZORPAY_BASE_URL + endpoint

                    # Create the payload for the patch request
                    patch_data = {
                        'settlements': settlements_data,
                        'tnc_accepted': tnc_accepted
                    }
                    response = razorpay_request(f"/v2/accounts/{account_data.get('id', '')}/products/{product_id}/", "patch", data=patch_data)
                    if response.status_code == 200:
                        serializer = PatchRequestSerializer(data=patch_data)
                        serializer.is_valid(raise_exception=True)

                        data = serializer.validated_data
                        product.settlements_account_number = data['settlements']['account_number']
                        product.settlements_ifsc_code = data['settlements']['ifsc_code']
                        product.settlements_beneficiary_name = data['settlements']['beneficiary_name']
                        product.tnc_accepted = data['tnc_accepted']
                        product.save()
                        # response = requests.patch(url, json=patch_data, headers=headers)

                        return Response({
                            "result": True,
                            "data": response.json(),
                            "message": PRODUCT_AND_BANK_DETAIL_SUCESS_MESSAGE,
                        }, status=status.HTTP_200_OK)
                    return error_response(ACCOUNT_PRODUCT_UPDATION_FAIL_MESSAGE, status.HTTP_400_BAD_REQUEST)

                return error_response(CREATE_PRODUCT_FAIL_MESSAGE, status.HTTP_400_BAD_REQUEST)

            return error_response(CREATE_PRODUCT_FAIL_MESSAGE, status.HTTP_400_BAD_REQUEST)

        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


# class AccountGetApi(APIView):
#     authentication_classes = (JWTAuthentication,)
#     permission_classes = (permissions.IsAuthenticated,)

#     def get(self, request):
#         try:
#             owner_id = request.user.id
#             if not owner_id:
#                 return error_response(OWNER_ID_NOT_PROVIDED_MESSAGE, status.HTTP_400_BAD_REQUEST)
#             try:
#                 account = OwnerBankingDetail.objects.get(hotel_owner_id=owner_id, status=True)
#             except OwnerBankingDetail.DoesNotExist:
#                 return error_response(PROVIDER_NOT_FOUND_MESSAGE, status.HTTP_400_BAD_REQUEST)
#             return generate_response(account, DATA_CREATE_MESSAGE, status.HTTP_200_OK, AccountSerializer)
#         except Exception:
#             return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


class AccountListView(ListAPIView):
    authentication_classes = (JWTAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = AccountSerializer
    pagination_class = CustomPagination

    def get_queryset(self):
        try:
            queryset = OwnerBankingDetail.objects.filter(hotel_owner=self.request.user).order_by('created_at')
            return queryset
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


class AccountUpdateApi(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def patch(self, request, id):
        try:
            account = OwnerBankingDetail.objects.get(id=id)
            serializer = HotelOwnerBankingSerializer(account, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return generate_response(serializer.data, ACCOUNT_DETAIL_UPDATE_MESSAGE, status.HTTP_200_OK)
        except OwnerBankingDetail.DoesNotExist:
            return error_response(BANKING_DETAIL_NOT_EXIST_MESSAGE, status.HTTP_400_BAD_REQUEST)
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


class BookingListView(ListAPIView):
    authentication_classes = (JWTAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = BookingHistorySerializer
    pagination_class = CustomPagination
    filterset_class = BookingFilter
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        try:
            queryset = BookingHistory.objects.filter(property__owner=self.request.user, book_status=True, is_cancel=False).order_by('created_at')
            return queryset
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


class BookingRetrieveView(RetrieveAPIView):
    authentication_classes = (JWTAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = BookingRetrieveSerializer

    def get_queryset(self):
        queryset = BookingHistory.objects.filter(property__owner=self.request.user, book_status=True).order_by('-created_at')
        return queryset

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            return generate_response(instance, DATA_RETRIEVAL_MESSAGE, status.HTTP_200_OK, self.serializer_class)
        except Http404:
            return error_response(OBJECT_NOT_FOUND_MESSAGE, status.HTTP_400_BAD_REQUEST)
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


class TransactionListView(ListAPIView):
    authentication_classes = (JWTAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = TransactionSerializer
    pagination_class = CustomPagination
    filterset_class = TransactionFilter
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        queryset = BookingHistory.objects.filter(property__owner=self.request.user).order_by('-created_at')
        return queryset

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())

            page = self.paginate_queryset(queryset)
            if page is not None:
                queryset = page

            grouped_data = defaultdict(list)
            for obj in queryset:
                serializer = self.get_serializer(obj)
                data = serializer.data
                created_at = data['created_at']
                created_at_date = parse_datetime(created_at).date()
                grouped_data[str(created_at_date)].append(data)

            result_data = []
            for created_at, bookings in grouped_data.items():
                result_data.append({
                    "created_at": created_at,
                    "data": bookings
                })
            if page is not None:
                return self.get_paginated_response(result_data)
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


class SubscriptionPlanView(ListAPIView):
    authentication_classes = (JWTAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    pagination_class = CustomPagination
    queryset = SubscriptionPlan.objects.all()
    serializer_class = SubscriptionPlanSerializer


class SubscriptionView(APIView):
    authentication_classes = (JWTAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    pagination_class = CustomPagination

    def get(self, request, *args, **kwargs):
        try:
            instance = SubscriptionTransaction.objects.filter(owner=self.request.user, payment_status=True).order_by('-created_at').first()
            if instance is None:
                return error_response(OBJECT_NOT_FOUND_MESSAGE, status.HTTP_400_BAD_REQUEST)
            plan_expire = check_plan_expiry(instance)
            if plan_expire:
                return error_response(PLAN_EXPIRY_MESSAGE, status.HTTP_400_BAD_REQUEST)
            return generate_response(instance, DATA_RETRIEVAL_MESSAGE, status.HTTP_200_OK, SubscriptionOutSerializer)
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)

    def post(self, request, *args, **kwargs):
        try:
            plan_id = request.data.get('subscription_plan')
            plan = get_object_or_404(SubscriptionPlan, id=plan_id)
            serializer = SubscriptionSerializer(data=request.data)
            if serializer.is_valid():
                razorpay_subscription = razorpay_client.subscription.create({
                    'plan_id': plan.razorpay_plan_id,
                    'customer_notify': 1,
                    'quantity': 1,
                    'total_count': 1,
                })
                instance = serializer.save(owner=self.request.user,
                                           subscription_plan=plan,
                                           razorpay_subscription_id=razorpay_subscription['id'])
                return generate_response(instance, DATA_CREATE_MESSAGE, status.HTTP_200_OK, SubscriptionOutSerializer)
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


class RatingsListView(ListAPIView):
    authentication_classes = (JWTAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    pagination_class = CustomPagination

    def list(self, request, *args, **kwargs):
        try:
            property = Property.objects.filter(owner=self.request.user).first()
            ratings = Ratings.objects.filter(property=property).order_by('-created_at')
            page = self.paginate_queryset(ratings)
            serializer = RatingsOutSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


class CancelBookingView(APIView):
    authentication_classes = (JWTAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )

    def post(self, request, *args, **kwargs):
        try:
            id = self.kwargs.get('id')
            booking = BookingHistory.objects.get(id=id)
            check_in_date = booking.check_in_date.date()
            current_date = now().date()
            cancellations_this_month = BookingHistory.objects.filter(
                property__owner=self.request.user,
                cancel_by_owner=True,
                cancel_date__year=now().year,
                cancel_date__month=now().month
            ).count()
            if cancellations_this_month >= 2:
                return error_response(CANCELLATION_LIMIT_MESSAGE, status.HTTP_400_BAD_REQUEST)
            days_before_check_in = (check_in_date - current_date).days
            days_before_check_in = get_days_before_check_in(booking, days_before_check_in)
            refund_amount = booking.amount

            if days_before_check_in <= 1:
                refund_response = razorpay_request(f"/v1/payments/{booking.payment_id}/refund", "post", data={"amount": refund_amount * 100,
                                                                                                              "reverse_all": 1})
                serializer = CancelBookingSerializer(booking, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save(is_cancel=True, cancel_date=now(), cancel_by_owner=True)
                    return deletion_success_response(REFUND_SUCCESFULL_MESSAGE, status.HTTP_200_OK)
                else:
                    return error_response(REFUND_ERROR_MESSAGE, status.HTTP_400_BAD_REQUEST)
            else:
                order_response = razorpay_request(f"/v1/transfers/{booking.transfer_id}", "patch", data={"on_hold": 1})
                if order_response.status_code != 200:
                    return error_response(ORDER_ERROR_MESSAGE, status.HTTP_400_BAD_REQUEST)
                refund_response = razorpay_request(f"/v1/payments/{booking.payment_id}/refund", "post", data={"amount": refund_amount * 100})
                if refund_response.status_code != 200:
                    return error_response(REFUND_ERROR_MESSAGE, status.HTTP_400_BAD_REQUEST)
                serializer = CancelBookingSerializer(booking, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save(is_cancel=True, cancel_date=now())
                    return deletion_success_response(REFUND_SUCCESFULL_MESSAGE, status.HTTP_200_OK)
                else:
                    return error_response(REFUND_ERROR_MESSAGE, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


@csrf_exempt
def razorpay_webhook(request):
    print("Received Razorpay webhook call")
    webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET

    body = request.body.decode('utf-8')
    received_signature = request.headers.get('X-Razorpay-Signature')
    dig = hmac.new(bytearray(webhook_secret, 'utf-8'), msg=body.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()

    if hmac.compare_digest(dig, received_signature):
        print("Signature verified successfully")
        payload = json.loads(body)
        if payload['event'] == 'payment.captured':
            print(f"Event: {payload['event']}")
            order_id = payload['payload']['payment']['entity']['order_id']
            payment_id = payload['payload']['payment']['entity']['id']
            try:
                booking = BookingHistory.objects.get(order_id=order_id)
                booking.payment_id = payment_id
                booking.book_status = True
                booking.save()
                print("TRUEE BOOK")
                return HttpResponse(status=200)
            except BookingHistory.DoesNotExist:
                return HttpResponse(status=404)
        elif payload['event'] == 'subscription.completed':
            print(f"Event: {payload['event']}")
            subscription_id = payload['payload']['subscription']['entity']['id']
            try:
                subscription = SubscriptionTransaction.objects.get(razorpay_subscription_id=subscription_id)
                subscription.payment_status = True
                subscription.save()
                print("TRUEE")
                return HttpResponse(status=200)
            except BookingHistory.DoesNotExist:
                return HttpResponse(status=404)
    else:
        print("Signature verification failed")
        return HttpResponse(status=400)
    return HttpResponse(status=500)
