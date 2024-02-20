from django.urls import path
from .views import CustomerRegisterView, CustomerLoginView, CustomerProfileView, PropertyListView, PayNowView, PropertyRetriveView


urlpatterns = [
    path('register/', CustomerRegisterView.as_view()),
    path('login/', CustomerLoginView.as_view()),
    path('profile/', CustomerProfileView.as_view()),
    path('propertyList/', PropertyListView.as_view()),
    path('propertyRetrieve/<int:pk>/', PropertyRetriveView.as_view()),
    path('PayNow/', PayNowView.as_view())
]
