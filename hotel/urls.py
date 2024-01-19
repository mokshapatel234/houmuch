from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PropertyViewSet, HotelRegisterView, HotelLoginView, OwnerProfileView, MasterRetrieveView


router = DefaultRouter()
router.register(r'properties', PropertyViewSet, basename='property')

urlpatterns = [
    path('register/', HotelRegisterView.as_view()),
    path('login/', HotelLoginView.as_view()),
    path('ownerProfile/', OwnerProfileView.as_view(), name="owner_profile"),
    # path('addProperty', PropertyCreateView.as_view(), name="add_property"),
    path('masterRetrieve/', MasterRetrieveView.as_view(), name="master_retrieve"),
    path('', include(router.urls)),  # Include the router URLs
]
