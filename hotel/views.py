from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from .models import Owner, PropertyType, RoomType, BedType, \
    BathroomType, RoomFeature, CommonAmenities, Property, OTP, RoomInventory
from .serializer import RegisterSerializer, LoginSerializer, OwnerProfileSerializer, \
    PropertySerializer, PropertyOutSerializer, PropertyTypeSerializer, RoomTypeSerializer, \
    BedTypeSerializer, BathroomTypeSerializer, RoomFeatureSerializer, CommonAmenitiesSerializer, \
    OTPVerificationSerializer, UpdatedPeriodSerializer, RoomInventorySerializer, RoomInventoryOutSerializer
from .utils import generate_token, model_name_to_snake_case, generate_response, generate_otp, send_otp_email, \
    error_response, deletion_success_response
from hotel_app_backend.messages import PHONE_REQUIRED_MESSAGE, PHONE_ALREADY_PRESENT_MESSAGE, \
    REGISTRATION_SUCCESS_MESSAGE, EXCEPTION_MESSAGE, LOGIN_SUCCESS_MESSAGE, \
    NOT_REGISTERED_MESSAGE, OWNER_NOT_FOUND_MESSAGE, PROFILE_MESSAGE, PROFILE_UPDATE_MESSAGE, \
    PROFILE_ERROR_MESSAGE, DATA_RETRIEVAL_MESSAGE, DATA_CREATE_MESSAGE, DATA_UPDATE_MESSAGE, \
    EMAIL_ALREADY_PRESENT_MESSAGE, OTP_VERIFICATION_SUCCESS_MESSAGE, OTP_VERIFICATION_INVALID_MESSAGE, \
    INVALID_INPUT_MESSAGE, OBJECT_NOT_FOUND_MESSAGE, DATA_DELETE_MESSAGE
from .authentication import JWTAuthentication
from rest_framework.generics import ListAPIView
from .paginator import CustomPagination
from django.contrib.gis.geos import Point
from django.http import Http404


class HotelRegisterView(APIView):
    permission_classes = (permissions.AllowAny, )

    def post(self, request):
        try:
            serializer = RegisterSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            phone_number = serializer.validated_data.get('phone_number')
            if not phone_number:
                return error_response(PHONE_REQUIRED_MESSAGE, status.HTTP_400_BAD_REQUEST)
            if Owner.objects.filter(phone_number=phone_number).exists():
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
            property_count = Property.objects.filter(owner=request.user).count()
            response_data = {
                'result': True,
                'data': {
                    **serializer.data,
                    "is_property_added": True if property_count >= 1 else False,
                    "property_count": property_count
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
                        send_otp_email(email, otp, 'OTP Verification', 'otp.html')

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


class MasterRetrieveView(ListAPIView):
    authentication_classes = (JWTAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )

    def list(self, request, *args, **kwargs):
        try:
            models_and_serializers = {
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
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            instance = serializer.save(owner=self.request.user)
            if location_data:
                instance.location = Point(location_data['coordinates'])
                instance.save()
            if room_types_data:
                instance.room_types.set(room_types_data)
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
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            updated_instance = serializer.save()
            if location_data:
                updated_instance.location = Point(location_data['coordinates'])
                updated_instance.save()
            if room_types_data:
                updated_instance.room_types.set(room_types_data)
            return generate_response(updated_instance, DATA_UPDATE_MESSAGE, status.HTTP_200_OK, PropertyOutSerializer)
        except Property.DoesNotExist:
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

    def create(self, request):
        try:
            property_id = request.GET.get('property_id')
            room_features = request.data.get('room_features', None)
            common_amenities = request.data.get('common_amenities', None)
            updated_period_data = request.data.pop('updated_period', None)
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            property_instance = Property.objects.get(id=property_id)
            instance = serializer.save(property=property_instance)
            if updated_period_data:
                updated_period_serializer = UpdatedPeriodSerializer(data=updated_period_data)
                updated_period_serializer.is_valid(raise_exception=True)
                updated_period_instance = updated_period_serializer.save()
                instance.updated_period = updated_period_instance
                instance.save()
            if room_features:
                instance.room_features.set(room_features)
            if common_amenities:
                instance.common_amenities.set(common_amenities)
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
            queryset = RoomInventory.objects.filter(property__owner=request.user).order_by('-id')
            page = self.paginate_queryset(queryset)
            serializer = RoomInventoryOutSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        except Exception:
            return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            room_features = request.data.get('room_features', None)
            common_amenities = request.data.get('common_amenities', None)
            updated_period_data = request.data.pop('updated_period', None)
            serializer = self.get_serializer(instance, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            updated_instance = serializer.save()
            if updated_period_data:
                updated_period_serializer = UpdatedPeriodSerializer(data=updated_period_data)
                updated_period_serializer.is_valid(raise_exception=True)
                updated_period_instance = updated_period_serializer.save()
                updated_instance.updated_period = updated_period_instance
                updated_instance.save()
            if room_features:
                updated_instance.room_features.set(room_features)
            if common_amenities:
                updated_instance.common_amenities.set(common_amenities)
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
