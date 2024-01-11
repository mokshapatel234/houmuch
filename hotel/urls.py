from django.urls import path
from .views import *

urlpatterns = [
    path('register',HotelRegisterView.as_view()),
    path('login',HotelLoginView.as_view()),

]
