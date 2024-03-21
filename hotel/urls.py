from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PropertyViewSet, HotelRegisterView, HotelLoginView, OwnerProfileView, \
    MasterRetrieveView, RoomInventoryViewSet, OTPVerificationView, CategoryRetrieveView, \
    BookingListView, AccountCreateApi, AccountUpdateApi, AccountGetApi, SubscriptionView, \
    SubscriptionPlanView, TransactionListView, RatingsListView


router = DefaultRouter()
router.register(r'properties', PropertyViewSet, basename='property')
router.register(r'roomInventories', RoomInventoryViewSet, basename='room_inventory')


urlpatterns = [
    path('register/', HotelRegisterView.as_view()),
    path('login/', HotelLoginView.as_view()),
    path('ownerProfile/', OwnerProfileView.as_view(), name="owner_profile"),
    path('categoryRetrieve/', CategoryRetrieveView.as_view(), name="category_retrieve"),
    path('masterRetrieve/', MasterRetrieveView.as_view(), name="master_retrieve"),
    path('verifyOtp/', OTPVerificationView.as_view(), name='otp_verification'),
    path('createAccount/', AccountCreateApi.as_view()),
    path('updateAccount/<int:id>/', AccountUpdateApi.as_view()),
    path('getAccount/', AccountGetApi.as_view()),
    path('bookingHistory/', BookingListView.as_view(), name='booking_history'),
    path('transactions/', TransactionListView.as_view(), name='transaction_history'),
    path('subscriptionPlan/', SubscriptionPlanView.as_view(), name='subscription_plan'),
    path('subscription/', SubscriptionView.as_view(), name='subscription'),
    path('ratings/', RatingsListView.as_view(), name='rating_list'),
    path('', include(router.urls)),
]
