from django.urls import path
from .views import CustomerRegisterView, CustomerLoginView, CustomerProfileView, HotelRetrieveView, PayNowView


urlpatterns = [
    path('register/', CustomerRegisterView.as_view()),
    path('login/', CustomerLoginView.as_view()),
    path('profile/', CustomerProfileView.as_view()),
    path('hotelRetrieve/', HotelRetrieveView.as_view()),
    path('PayNow/', PayNowView.as_view())
]
