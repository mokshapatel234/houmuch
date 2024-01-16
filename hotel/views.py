from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Owner, FCMToken, PropertyType, RoomType, BedType, BathroomType, RoomFeature, CommonAmenities
from .serializer import *
from .utils import generate_token, model_name_to_snake_case
from hotel_app_backend.messages import *
from .authentication import JWTAuthentication
from rest_framework.generics import ListAPIView


class HotelRegisterView(APIView):
    permission_classes = (permissions.AllowAny, )

    def post(self, request):
        try:
            serializer = RegisterSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            phone_number = serializer.validated_data.get('phone_number')
            fcm_token = request.data.get('fcm_token')

            if not phone_number:
                return Response({'result': False, 'message': PHONE_REQUIRED_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)

            if Owner.objects.filter(phone_number=phone_number).exists():
                return Response({'result': False, 'message': PHONE_ALREADY_PRESENT_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)
             
            else:
                serializer.save()
                user_id = serializer.instance.id

                if fcm_token:
                    FCMToken.objects.create(user_id=user_id, fcm_token=fcm_token, is_owner=True)

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


class HotelLoginView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        try:
            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            phone = serializer.validated_data.get('phone_number')
            fcm_token = request.data.get('fcm_token')

            try:
                hotel_owner = Owner.objects.get(phone_number=phone)
                if hotel_owner.is_verified:
                    if fcm_token:
                        FCMToken.objects.create(user_id=hotel_owner.id, fcm_token=fcm_token, is_owner=True)

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
                else:
                    return Response({'result': False, 'message': OWNER_NOT_VERIFIED_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)

            except Owner.DoesNotExist:
                return Response({'result': False, 'message': NOT_REGISTERED_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)

        except Exception:
            return Response({'result': False, 'message': EXCEPTION_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)


class OwnerProfileView(APIView):
    authentication_classes = (JWTAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )

    def get(self,request):
        try:
            serializer = OwnerProfileSerializer(request.user)
    
            return Response({"result": True,
                            "data": serializer.data,
                            "message": PROFILE_MESSAGE}, status=status.HTTP_200_OK)
        except Owner.DoesNotExist:
            return Response({'result': False, 'message': OWNER_NOT_FOUND_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'result': False, 'message': EXCEPTION_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        try:
            serializer = OwnerProfileSerializer(request.user, data=request.data, partial=True)
            if serializer.is_valid():

                email = serializer.validated_data.get('email', None)
                phone_number = serializer.validated_data.get('phone_number', None)

                if phone_number and Owner.objects.filter(phone_number=phone_number):
                    return Response({'result': False, 'message': PHONE_ALREADY_PRESENT_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)
                if email and Owner.objects.filter(email=email):
                    return Response({'result': False, 'message': EMAIL_ALREADY_PRESENT_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)

                serializer.save()
                return Response({"result": True,
                                "data": serializer.data,
                                'message': PROFILE_UPDATE_MESSAGE},status=status.HTTP_201_CREATED)
            else:
                return Response({"result": False,
                                "message": PROFILE_ERROR_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)

        except Exception:
            return Response({'result': False, 'message': EXCEPTION_MESSAGE}, status=status.HTTP_400_BAD_REQUEST)


class MasterRetrieveView(ListAPIView):
    authentication_classes = (JWTAuthentication, )
    permission_classes = (permissions.IsAuthenticated, )

    def list(self, request, *args, **kwargs):
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

        return Response(data)