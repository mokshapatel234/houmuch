from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PropertyViewSet, HotelRegisterView, HotelLoginView, OwnerProfileView, \
    MasterRetrieveView, RoomInventoryViewSet, OTPVerificationView, CategoryRetrieveView, \
    BookingListView, AccountCreateApi, AccountUpdateApi, AccountGetApi, SubscriptionView, \
    SubscriptionPlanView


router = DefaultRouter()
router.register(r'properties', PropertyViewSet, basename='property')
router.register(r'roomInventories', RoomInventoryViewSet, basename='room_inventory')
# router.register(r'subscription', SubscriptionViewSet, basename='property')

urlpatterns = [
    path('register/', HotelRegisterView.as_view()),
    path('login/', HotelLoginView.as_view()),
    path('ownerProfile/', OwnerProfileView.as_view(), name="owner_profile"),
    path('categoryRetrieve/', CategoryRetrieveView.as_view(), name="category_retrieve"),
    path('masterRetrieve/', MasterRetrieveView.as_view(), name="master_retrieve"),
    path('verifyOtp/', OTPVerificationView.as_view(), name='otp_verification'),
    path('create-account/', AccountCreateApi.as_view()),
    path('update-account/', AccountUpdateApi.as_view()),
    path('get-account/', AccountGetApi.as_view()),
    path('bookingHistory/', BookingListView.as_view(), name='booking_history'),
    path('subscriptionPlan/', SubscriptionPlanView.as_view(), name='subscription_plan'),
    path('subscription/', SubscriptionView.as_view(), name='subscription'),
    path('', include(router.urls)),  # Include the router URLs
]
