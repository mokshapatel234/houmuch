from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Customer
from hotel.models import Property, Owner, PropertyType, RoomInventory, RoomType, BathroomType, BookingHistory, GuestDetail
from django.contrib.gis.geos import Point
from unittest.mock import patch
from datetime import date, timedelta
from django.utils import timezone


class BaseCustomerViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer_data = {
            'phone_number': '1234567890',
            'device_id': 'device_id',
            'fcm_token': 'new_fcm',
        }
        self.customer = self.create_customer()
        self.token = None
        self.login_customer()

    def create_customer(self):
        return Customer.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone_number=self.customer_data['phone_number'],
            profile_image="profile.jpg",
            address="Sample Address",
            government_id="1234567890",
            fcm_token=self.customer_data['fcm_token'],
            device_id=self.customer_data['device_id']
        )

    def login_customer(self):
        response = self.client.post('/customer/login/', self.customer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.token = response.data['data'].get('token')

    def create_property(self):
        self.hotel = Owner.objects.create(
            phone_number="1234567890",
            hotel_name="Hotel 1",
            address="This is address"
        )

        property_type_instance = PropertyType.objects.create(property_type='Hotel')
        return Property.objects.create(
            parent_hotel_group="Parent Group",
            hotel_nick_name="Hotel Nick Name",
            manager_name="Manager Name",
            hotel_phone_number="1234567890",
            hotel_website="http://samplehotel.com",
            number_of_rooms=50,
            check_in_time="12:00 PM",
            check_out_time="12:00 PM",
            location=Point(12.971598, 77.594562),
            nearby_popular_landmark="Nearby Landmark",
            owner=self.hotel,
            property_type=property_type_instance,
            commission_percent=10.0,
            hotel_class=3,
            pet_friendly=True,
            breakfast_included=True,
            is_cancellation=True,
            status=True,
            is_online=True,
            is_verified=True
        )

    def create_booking(self):
        property_instance = self.create_property()
        return BookingHistory.objects.create(
            property=property_instance,
            customer=self.customer,
            property_deal=None,
            num_of_rooms=2,
            rooms=None,
            order_id="123456789",
            transfer_id=None,
            check_in_date=timezone.now(),
            check_out_date=timezone.now() + timezone.timedelta(days=1),
            amount=500.00,
            currency="USD",
            is_cancel=False,
            cancel_by_owner=False,
            cancel_date=None,
            cancel_reason=None,
            book_status=True,
            payment_id="payment123",
            is_confirmed=True
        )


class CustomerRegisterViewTest(BaseCustomerViewTest):
    def test_valid_customer_registration(self):
        valid_data = {
            "phone_number": "4569871230",
            "first_name": "Customer1",
            "last_name": "Name",
            "fcm_token": "new_fcm",
            "device_id": "device_id"
        }
        response = self.client.post('/customer/register/', valid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_invalid_customer_registration(self):
        invalid_data = {
            "phone_number": "4569871230",
            "first_name": "Customer1"
        }
        response = self.client.post('/customer/register/', invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CustomerProfileViewTest(BaseCustomerViewTest):
    def test_customer_profile_view_get(self):
        self.client.force_authenticate(user=self.customer, token=self.token)
        response = self.client.get('/customer/profile/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_customer_profile_view_patch(self):
        self.client.force_authenticate(user=self.customer, token=self.token)
        update_data = {'first_name': 'Updated', 'last_name': 'Name', 'email': 'customer@yopmail.com'}
        response = self.client.patch('/customer/profile/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_customer_profile_view_patch_invalid_phone(self):
        self.client.force_authenticate(user=self.customer, token=self.token)
        invalid_data = {'phone_number': '1234567890'}
        response = self.client.patch('/customer/profile/', invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_customer_profile_view_patch_invalid_data(self):
        self.client.force_authenticate(user=self.customer, token=self.token)
        invalid_data = {'phone_number': '123456789@'}
        response = self.client.patch('/customer/profile/', invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PropertyListViewTest(BaseCustomerViewTest):
    def get_property_list(self):
        self.client.force_authenticate(user=self.customer, token=self.token)  # Authenticate as customer
        return self.client.get('/customer/propertyList/')

    def test_property_list_view(self):
        self.create_property()
        response = self.get_property_list()
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RoomListViewTest(BaseCustomerViewTest):
    def get_room_list(self):
        self.client.force_authenticate(user=self.customer, token=self.token)
        response = self.client.get(f'/customer/roomList/{self.property.id}/')
        return response

    def create_property_and_mock_rooms(self):
        self.property = self.create_property()
        with patch('customer.views.RoomInventory.objects.filter') as mock_filter:
            mock_queryset = RoomInventory.objects.none()  # Mock an empty queryset
            mock_filter.return_value = mock_queryset
            response = self.get_room_list()
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_room_list_view(self):
        self.create_property_and_mock_rooms()


class RoomRetrieveViewTest(BaseCustomerViewTest):
    def authenticate_and_create_url(self, room_pk):
        self.client.force_authenticate(user=self.customer, token=self.token)
        url = f'/customer/roomRetrieve/{room_pk}/'
        return url

    def test_retrieve_room_success(self):
        self.property = self.create_property()

        room_type = RoomType.objects.create(room_type='Suite')
        bathroom_type = BathroomType.objects.create(bathroom_type='Private')
        self.room = RoomInventory.objects.create(
            property=self.property,
            room_name="Example Room",
            floor=1,
            room_view="Example View",
            area_sqft=500,
            room_type=room_type,
            bathroom_type=bathroom_type,
            adult_capacity=2,
            children_capacity=1,
            default_price=100,
            min_price=80,
            max_price=120,
            is_verified=True,
            status=True
        )

        self.url = self.authenticate_and_create_url(self.room.pk)
        with patch('customer.views.RoomInventory.objects.get') as mock_get:
            mock_get.return_value = self.room
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)


class OrderSummaryViewTest(BaseCustomerViewTest):
    def authenticate_and_request_order_summary(self, query_params):
        self.client.force_authenticate(user=self.customer, token=self.token)
        return self.client.get('/customer/orderSummary/', query_params)

    @patch('customer.views.RoomInventory.objects.get')
    def test_order_summary_success(self, mock_get):
        booking = self.create_booking()

        room_type = RoomType.objects.create(room_type='Suite')
        bathroom_type = BathroomType.objects.create(bathroom_type='Private')
        self.room = RoomInventory.objects.create(
            property=booking.property,
            room_name="Example Room",
            floor=1,
            room_view="Example View",
            area_sqft=500,
            room_type=room_type,
            bathroom_type=bathroom_type,
            adult_capacity=2,
            children_capacity=1,
            default_price=100,
            min_price=80,
            max_price=120,
            is_verified=True,
            status=True
        )
        mock_get.return_value = self.room

        # Set up query parameters for the request
        query_params = {
            'room_id': self.room.id,
            'check_in_date': date.today().isoformat(),
            'check_out_date': (date.today() + timedelta(days=1)).isoformat(),
            'num_of_rooms': 1
        }

        response = self.authenticate_and_request_order_summary(query_params)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class BookingListViewTest(BaseCustomerViewTest):
    def test_booking_list_view(self):
        self.create_booking()
        self.client.force_authenticate(user=self.customer, token=self.token)
        response = self.client.get('/customer/bookingHistory/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class BookingRetrieveViewTest(BaseCustomerViewTest):
    def get_booking(self, booking_id):
        self.client.force_authenticate(user=self.customer, token=self.token)
        return self.client.get(f'/customer/bookingRetrieve/{booking_id}/')

    def create_booking_and_guest_detail(self):
        self.booking_history = self.create_booking()

        # Create a guest detail for the booking
        self.guest_detail = GuestDetail.objects.create(
            booking=self.booking_history,
            no_of_adults=2,
            no_of_children=1,
            age_of_children="5,7",
        )

    def test_booking_retrieve_view(self):
        self.create_booking_and_guest_detail()
        response = self.get_booking(self.booking_history.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RatingsTest(BaseCustomerViewTest):
    def create_property_and_authenticate(self):
        self.property = self.create_property()

    def generate_rating_url(self, property_id):
        self.client.force_authenticate(user=self.customer, token=self.token)
        return f'/customer/ratings/{property_id}/'

    def test_create_rating(self):
        self.create_property_and_authenticate()
        url = self.generate_rating_url(self.property.id)
        payload = {
            'ratings': 4,
            'review': 'Great property!'
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
