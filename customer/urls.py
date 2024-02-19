from django.urls import path
from .views import CustomerRegisterView, CustomerLoginView, CustomerProfileView, HotelRetrieveView, CustomerSessionView


urlpatterns = [
    path('register/', CustomerRegisterView.as_view()),
    path('login/', CustomerLoginView.as_view()),
    path('profile/', CustomerProfileView.as_view()),
    path('hotelRetrieve/', HotelRetrieveView.as_view()),
    path('setsession/', CustomerSessionView.as_view())
]
