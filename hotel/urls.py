from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PropertyViewSet, HotelRegisterView, HotelLoginView, OwnerProfileView, \
    MasterRetrieveView, RoomInventoryViewSet, OTPVerificationView, CategoryRetrieveView, \
    BookingListView, AccountCreateApi, AccountUpdateApi, SubscriptionView, \
    SubscriptionPlanView, TransactionListView, RatingsListView, CancelBookingView, \
    BookingRetrieveView, AccountGetApi, UpdateInventoryList, DealListView


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
    path('getAccount/', AccountGetApi.as_view(), name='account_get'),
    # path('getAccountList/', AccountListView.as_view(), name='account_list'),
    path('bookingHistory/', BookingListView.as_view(), name='booking_history'),
    path('transactions/', TransactionListView.as_view(), name='transaction_history'),
    path('subscriptionPlan/', SubscriptionPlanView.as_view(), name='subscription_plan'),
    path('subscription/', SubscriptionView.as_view(), name='subscription'),
    path('ratings/', RatingsListView.as_view(), name='rating_list'),
    path('cancelBooking/<int:id>/', CancelBookingView.as_view(), name="vendor_cancel_booking"),
    path('bookingRetrieve/<int:pk>/', BookingRetrieveView.as_view(), name='booking_retrieve'),
    path('updateInventory/<int:id>/', UpdateInventoryList.as_view(), name='update_inventory'),
    path('dealHistory/', DealListView.as_view(), name="Deal History"),
    path('', include(router.urls)),
]
