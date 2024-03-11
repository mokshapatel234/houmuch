from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from .models import Owner, PropertyType, RoomType, BedType, \
    BathroomType, RoomFeature, CommonAmenities, Property, OTP, \
    RoomInventory, RoomImage, Category, PropertyImage, \
    PropertyCancellation, BookingHistory, Product, OwnerBankingDetail, \
    SubscriptionPlan, SubscriptionTransaction
from .serializer import RegisterSerializer, LoginSerializer, OwnerProfileSerializer, \
    PropertySerializer, PropertyOutSerializer, PropertyTypeSerializer, RoomTypeSerializer, \
    BedTypeSerializer, BathroomTypeSerializer, RoomFeatureSerializer, CommonAmenitiesSerializer, \
    OTPVerificationSerializer, UpdatedPeriodSerializer, RoomInventorySerializer, RoomInventoryOutSerializer, \
    CategorySerializer, PropertyImageSerializer, BookingHistorySerializer, HotelOwnerBankingSerializer, \
    PatchRequestSerializer, AccountSerializer, SubscriptionPlanSerializer, SubscriptionSerializer, SubscriptionOutSerializer
from .utils import generate_token, model_name_to_snake_case, generate_response, generate_otp, send_mail, \
    error_response, deletion_success_response, remove_cache, cache_response, set_cache, check_plan_expiry
from hotel_app_backend.messages import PHONE_REQUIRED_MESSAGE, PHONE_ALREADY_PRESENT_MESSAGE, \
    REGISTRATION_SUCCESS_MESSAGE, EXCEPTION_MESSAGE, LOGIN_SUCCESS_MESSAGE, \
    NOT_REGISTERED_MESSAGE, OWNER_NOT_FOUND_MESSAGE, PROFILE_MESSAGE, PROFILE_UPDATE_MESSAGE, \
    PROFILE_ERROR_MESSAGE, DATA_RETRIEVAL_MESSAGE, DATA_CREATE_MESSAGE, DATA_UPDATE_MESSAGE, \
    EMAIL_ALREADY_PRESENT_MESSAGE, OTP_VERIFICATION_SUCCESS_MESSAGE, OTP_VERIFICATION_INVALID_MESSAGE, \
    INVALID_INPUT_MESSAGE, OBJECT_NOT_FOUND_MESSAGE, DATA_DELETE_MESSAGE, SENT_OTP_MESSAGE, PLAN_EXPIRY_MESSAGE, \
    ACCOUNT_ERROR_MESSAGE, CREATE_PRODUCT_FAIL_MESSAGE, OWNER_ID_NOT_PROVIDED_MESSAGE, PROVIDER_NOT_FOUND_MESSAGE, \
    ACCOUNT_PRODUCT_UPDATION_FAIL_MESSAGE, ACCOUNT_DETAIL_UPDATE_FAIL_MESSAGE, BANKING_DETAIL_NOT_EXIST_MESSAGE, \
    PRODUCT_AND_BANK_DETAIL_SUCESS_MESSAGE
from .authentication import JWTAuthentication
from rest_framework.generics import ListAPIView
from .paginator import CustomPagination
from django.contrib.gis.geos import Point
from django.http import Http404
from hotel_app_backend.utils import delete_image_from_s3, razorpay_client
from django.contrib.auth.models import User
from .filters import RoomInventoryFilter, BookingFilter, TransactionFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db.models import Case, When, Value, IntegerField
from django.conf import settings
import requests
from django.shortcuts import get_object_or_404
import hashlib, hmac, json


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
        except Exception:
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
            response_data = {
                'result': True,
                'data': {
                    **serializer.data,
                    "is_property_added": True if property.count() >= 1 else False,
                    "property_count": property.count() if property.count() >= 1 else 0,
                    "images": image_serializer.data
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
                return Response(response_data, status=status.HTTP_200_OK)
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
        serializer = super().list(request, *args, **kwargs)
        response_data = {
            'result': True,
            'data': serializer.data,
            'message': DATA_RETRIEVAL_MESSAGE,
        }
        return Response(response_data, status=status.HTTP_200_OK)


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
        except Exception:
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
            instance = serializer.save(property=property_instance)
            image_instances = []
            if updated_period_data:
                updated_period_serializer = UpdatedPeriodSerializer(data=updated_period_data)
                updated_period_serializer.is_valid(raise_exception=True)
                updated_period_serializer.save(room_inventory=instance)
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
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)

    def retrieve(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            return generate_response(instance, DATA_RETRIEVAL_MESSAGE, status.HTTP_200_OK, RoomInventoryOutSerializer)
        except Http404:
            return error_response(OBJECT_NOT_FOUND_MESSAGE, status.HTTP_400_BAD_REQUEST)
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        try:
            # cache_response("room_inventory_list", request.user)
            queryset = self.filter_queryset(RoomInventory.objects.filter(property__owner=request.user))
            page = self.paginate_queryset(queryset)
            serializer = RoomInventoryOutSerializer(page, many=True)
            response_data = self.get_paginated_response(serializer.data)
            # set_cache("room_inventory_list", request.user, serialized_data)
            return response_data
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
                updated_period_serializer = UpdatedPeriodSerializer(data=updated_period_data)
                updated_period_serializer.is_valid(raise_exception=True)
                updated_period_serializer.save(room_inventory=instance)
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
        except Exception:
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
            existing_account = OwnerBankingDetail.objects.filter(hotel_owner=request.user).first()
            if existing_account:
                return error_response(ACCOUNT_ERROR_MESSAGE, status.HTTP_400_BAD_REQUEST)

            endpoint = "/accounts"
            url = settings.RAZORPAY_BASE_URL + endpoint

            request.data['type'] = 'route'
            request.data['business_type'] = 'partnership'

            serializer = HotelOwnerBankingSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            settlements_data = request.data.pop('settlements', {})
            tnc_accepted = request.data.pop('tnc_accepted', False)

            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Basic cnpwX3Rlc3RfQmk0dnZ5WUlWbEdGZTg6TTB6aHhCNXlGaGpYU0Q4MGFtYnZtU3c5'
            }

            response = requests.post(url, json=request.data, headers=headers)

            if response.status_code == 200:
                account_data = response.json()
                instance = serializer.save(
                    hotel_owner=request.user,
                    status='active',
                    account_id=account_data.get('id', ''),
                    type='route',
                    business_type='partnership'
                )

                product_data = {
                    "product_name": "route"
                }

                endpoint = f"/accounts/{account_data.get('id', '')}/products"
                url = settings.RAZORPAY_BASE_URL + endpoint

                response = requests.post(url, json=product_data, headers=headers)

                if response.status_code == 200 and instance is not None:
                    product_data = response.json()
                    product_id = product_data.get("id")
                    product = Product(product_id=product_id)
                    product.owner_banking = instance
                    product.save()

                    endpoint = f"/accounts/{account_data.get('id', '')}/products/{product_id}/"
                    url = settings.RAZORPAY_BASE_URL + endpoint

                    # Create the payload for the patch request
                    patch_data = {
                        'settlements': settlements_data,
                        'tnc_accepted': tnc_accepted
                    }

                    serializer = PatchRequestSerializer(data=patch_data)
                    serializer.is_valid(raise_exception=True)

                    data = serializer.validated_data
                    product.settlements_account_number = data['settlements']['account_number']
                    product.settlements_ifsc_code = data['settlements']['ifsc_code']
                    product.settlements_beneficiary_name = data['settlements']['beneficiary_name']
                    product.tnc_accepted = data['tnc_accepted']
                    product.save()

                    response = requests.patch(url, json=patch_data, headers=headers)

                    if response.status_code == 200:
                        updated_product_data = response.json()

                        return Response({
                            "result": True,
                            "data": updated_product_data,
                            "message": PRODUCT_AND_BANK_DETAIL_SUCESS_MESSAGE,
                        }, status=status.HTTP_200_OK)
                    return error_response(ACCOUNT_PRODUCT_UPDATION_FAIL_MESSAGE, status.HTTP_400_BAD_REQUEST)

                return error_response(CREATE_PRODUCT_FAIL_MESSAGE, status.HTTP_400_BAD_REQUEST)

            return error_response(CREATE_PRODUCT_FAIL_MESSAGE, status.HTTP_400_BAD_REQUEST)

        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


class AccountGetApi(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        try:
            owner_id = request.user.id

            if not owner_id:
                return error_response(OWNER_ID_NOT_PROVIDED_MESSAGE, status.HTTP_400_BAD_REQUEST)

            try:
                account = OwnerBankingDetail.objects.get(hotel_owner_id=owner_id)
            except OwnerBankingDetail.DoesNotExist:
                return error_response(PROVIDER_NOT_FOUND_MESSAGE, status.HTTP_400_BAD_REQUEST)

            serializer = AccountSerializer(account)
            response_data = serializer.data

            response_data = {
                'result': True,
                'data': response_data,
                'message': DATA_RETRIEVAL_MESSAGE
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


class AccountUpdateApi(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (permissions.IsAuthenticated,)

    def patch(self, request):
        try:
            account_id = request.data.get('account_id', None)
            if not account_id:
                return error_response(OWNER_ID_NOT_PROVIDED_MESSAGE, status.HTTP_400_BAD_REQUEST)

            owner_banking_detail = OwnerBankingDetail.objects.get(account_id=account_id)

            owner_banking_detail.phone = request.data.get('phone', owner_banking_detail.phone)
            owner_banking_detail.legal_business_name = request.data.get('legal_business_name', owner_banking_detail.legal_business_name)
            owner_banking_detail.save()

            endpoint = f"/accounts/{account_id}"
            url = settings.RAZORPAY_BASE_URL + endpoint
            headers = {
                'Content-Type': 'application/json',
                'Authorization': 'Basic cnpwX3Rlc3RfQmk0dnZ5WUlWbEdGZTg6TTB6aHhCNXlGaGpYU0Q4MGFtYnZtU3c5'  # Use your Razorpay API key secret here
            }

            patch_data = {
                'phone': owner_banking_detail.phone,
                'legal_business_name': owner_banking_detail.legal_business_name
            }

            response = requests.patch(url, json=patch_data, headers=headers)

            if response.status_code == 200:
                updated_account_data = response.json()
                return Response({
                    "result": True,
                    "data": updated_account_data,
                    "message": "Account details updated successfully",
                }, status=status.HTTP_200_OK)
            else:
                return error_response(ACCOUNT_DETAIL_UPDATE_FAIL_MESSAGE, status.HTTP_400_BAD_REQUEST)

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
        today = timezone.now().date()
        queryset = BookingHistory.objects.annotate(
            is_today=Case(
                When(check_in_date__date=today, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).filter(property__owner=self.request.user, book_status=True).order_by('-is_today')
        return queryset
    

class TransactionListView(ListAPIView):
    authentication_classes = (JWTAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = BookingHistorySerializer
    pagination_class = CustomPagination
    filterset_class = TransactionFilter
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        queryset = BookingHistory.objects.filter(property__owner=self.request.user).order_by('-created_at')
        return queryset


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


def razorpay_webhook(request):
    webhook_secret = settings.RAZORPAY_WEBHOOK_SECRET

    body = request.body.decode('utf-8')
    received_signature = request.headers.get('X-Razorpay-Signature')

    dig = hmac.new(bytearray(webhook_secret, 'utf-8'), msg=body.encode('utf-8'), digestmod=hashlib.sha256).hexdigest()

    if hmac.compare_digest(dig, received_signature):
        payload = json.loads(body)

        if payload['event'] == 'payment.captured':
            order_id = payload['payload']['payment']['entity']['order_id']

            try:
                booking = BookingHistory.objects.get(order_id=order_id)
                booking.book_status = True
                booking.save()
                return Response({'status': 'success', 'message': 'Booking status updated successfully'})
            except BookingHistory.DoesNotExist:
                return Response({'status': 'failed', 'message': 'Booking not found'})
        else:
            return Response(status=200)
    else:
        return Response({'status': 'failed', 'message': 'Invalid signature'}, status=400)