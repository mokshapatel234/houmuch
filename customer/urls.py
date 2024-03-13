from django.urls import path
from .views import CustomerRegisterView, CustomerLoginView, CustomerProfileView, PropertyListView, PayNowView, \
    PropertyRetriveView, RoomInventoryListView, OrderSummaryView, RoomRetriveView, BookingListView, PropertyRatingView


urlpatterns = [
    path('register/', CustomerRegisterView.as_view()),
    path('login/', CustomerLoginView.as_view()),
    path('profile/', CustomerProfileView.as_view(), name='customer_profile'),
    path('propertyList/', PropertyListView.as_view(), name='property_list'),
    path('propertyRetrieve/<int:pk>/', PropertyRetriveView.as_view(), name='property_detail'),
    path('roomList/<int:property_id>/', RoomInventoryListView.as_view(), name='room_list'),
    path('roomRetrieve/<int:pk>/', RoomRetriveView.as_view(), name='room_detail'),
    path('PayNow/', PayNowView.as_view(), name='book_property'),
    path('orderSummary/', OrderSummaryView.as_view(), name='order_summary'),
    path('bookingHistory/', BookingListView.as_view(), name='booking_history'),
    path('ratings/<int:property_id>/', PropertyRatingView.as_view(), name='add_ratings'),

]
