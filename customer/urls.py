from django.urls import path
from .views import CustomerRegisterView, CustomerLoginView, CustomerProfileView


urlpatterns = [
    path('register/', CustomerRegisterView.as_view()),
    path('login/', CustomerLoginView.as_view()),
    path('profile/', CustomerProfileView.as_view()),
]
