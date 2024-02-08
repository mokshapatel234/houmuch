from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PropertyViewSet, HotelRegisterView, HotelLoginView, OwnerProfileView, \
    MasterRetrieveView, RoomInventoryViewSet, OTPVerificationView, CategoryRetrieveView


router = DefaultRouter()
router.register(r'properties', PropertyViewSet, basename='property')
router.register(r'roomInventories', RoomInventoryViewSet, basename='room_inventory')

urlpatterns = [
    path('register/', HotelRegisterView.as_view()),
    path('login/', HotelLoginView.as_view()),
    path('ownerProfile/', OwnerProfileView.as_view(), name="owner_profile"),
    path('categoryRetrieve/', CategoryRetrieveView.as_view(), name="category_retrieve"),
    path('masterRetrieve/', MasterRetrieveView.as_view(), name="master_retrieve"),
    path('verifyOtp/', OTPVerificationView.as_view(), name='otp-verification'),
    path('', include(router.urls)),  # Include the router URLs
]
