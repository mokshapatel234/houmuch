from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Owner, PropertyType, RoomFeature, RoomType, BathroomType, BedType, \
    CommonAmenities, Property, RoomInventory, Category, OwnerBankingDetail, \
    BookingHistory, SubscriptionPlan, SubscriptionTransaction, Ratings, GuestDetail
from django.contrib.gis.geos import Point
from django.contrib.auth.models import User
from customer.models import Customer
from django.utils import timezone


class BaseHotelViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.hotel = self.create_hotel()
        self.login_data = {
            'phone_number': '1234567890',
            'fcm_token': 'new_fcm',
        }
        self.token = None
        self.login_hotel()

    def create_hotel(self):
        return Owner.objects.create(
            phone_number="1234567890",
            hotel_name="Hotel 1",
            address="This is address"
        )

    def login_hotel(self):
        response = self.client.post('/hotel/login/', self.login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.token = response.data['data'].get('token')

    def create_property(self):
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

    def create_customer(self):
        return Customer.objects.create(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone_number="1234567890",
            profile_image="profile.jpg",
            address="Sample Address",
            government_id="1234567890",
            fcm_token="token",
            device_id="device_id"
        )

    def create_booking(self, property_instance, customer_instance):
        return BookingHistory.objects.create(
            property=property_instance,
            customer=customer_instance,
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


class HotelRegisterViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.valid_data = {
            "phone_number": "1234567890",
            "hotel_name": "Hotel 1",
            "address": "This is address",
            "email": "aqua771@gmail.com",
            "gst": "fr2345678kjgf"
        }

    def register_hotel_owner(self, data):
        return self.client.post('/hotel/register/', data, format='json')

    def test_valid_hotel_owner_registration(self):
        response = self.register_hotel_owner(self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_invalid_hotel_owner_registration(self):
        invalid_data = {
            "first_name": "Hotel Owner"
        }
        response = self.register_hotel_owner(invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class HotelLoginViewTest(BaseHotelViewTest):
    def test_hotel_login_success(self):
        response = self.client.post('/hotel/login/', self.login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_hotel_login_failure_not_registered(self):
        invalid_data = {'phone_number': '9876543210', 'fcm_token': 'new_fcm'}
        response = self.client.post('/hotel/login/', invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_hotel_login_failure(self):
        invalid_data = {'phhone_number': '1234567890', 'fcm_token': 'new_fcm'}
        response = self.client.post('/hotel/login/', invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class HotelOwnerProfileViewTest(BaseHotelViewTest):
    def test_hotel_profile_view_get(self):
        self.client.force_authenticate(user=self.hotel, token=self.token)
        response = self.client.get('/hotel/ownerProfile/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_hotel_profile_view_patch(self):
        self.client.force_authenticate(user=self.hotel, token=self.token)
        update_data = {'hotel_name': 'Updated', 'email': 'hotel@yopmail.com'}
        response = self.client.patch('/hotel/ownerProfile/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_hotel_profile_view_patch_invalid_phone(self):
        self.client.force_authenticate(user=self.hotel, token=self.token)
        invalid_data = {'phone_number': '1234567890'}
        response = self.client.patch('/hotel/ownerProfile/', invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_hotel_profile_view_patch_invalid_data(self):
        self.client.force_authenticate(user=self.hotel, token=self.token)
        invalid_data = {'phone_number': '123456789@'}
        response = self.client.patch('/hotel/ownerProfile/', invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class MasterRetrieveViewTest(BaseHotelViewTest):
    def test_master_retrieve_view(self):
        PropertyType.objects.create(property_type='Hotel')
        RoomType.objects.create(room_type='Suite')
        BedType.objects.create(bed_type='Queen')
        BathroomType.objects.create(bathroom_type='Private')
        RoomFeature.objects.create(room_feature='Balcony')
        CommonAmenities.objects.create(common_ameninity='WiFi')
        self.client.force_authenticate(user=self.hotel, token=self.token)
        response = self.client.get('/hotel/masterRetrieve/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CategoryRetrieveViewTest(BaseHotelViewTest):
    def test_category_retrieve_view(self):
        Category.objects.create(category='Test Category', bid_time_duration=60)
        self.client.force_authenticate(user=self.hotel, token=self.token)
        response = self.client.get('/hotel/categoryRetrieve/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class PropertyViewSetTest(BaseHotelViewTest):
    def create_property(self, data):
        self.client.force_authenticate(user=self.hotel, token=self.token)
        return self.client.post('/hotel/properties/', data, format='json')

    def retrieve_property(self, property_instance):
        self.client.force_authenticate(user=self.hotel, token=self.token)
        return self.client.get(f'/hotel/properties/{property_instance.id}/', format='json')

    def retrieve_exception_property(self, property_instance):
        self.client.force_authenticate(user=self.hotel, token=self.token)
        return self.client.get(f'/hotel/properties/{property_instance}/', format='json')

    def update_property(self, property_instance, data):
        self.client.force_authenticate(user=self.hotel, token=self.token)
        return self.client.patch(f'/hotel/properties/{property_instance.id}/', data, format='json')

    def update_exception_property(self, property_instance, data):
        self.client.force_authenticate(user=self.hotel, token=self.token)
        return self.client.patch(f'/hotel/properties/{property_instance}/', data, format='json')

    def list_property(self):
        self.client.force_authenticate(user=self.hotel, token=self.token)
        return self.client.get('/hotel/properties/', format='json')

    def test_property(self):
        User.objects.create_superuser(username='admin', email='admin@example.com', password='password')
        property_type = PropertyType.objects.create(property_type='Hotel')
        room_type = RoomType.objects.create(room_type='Suite')

        create_data = {
            "parent_hotel_group": "Updated group",
            "hotel_nick_name": "Nick name",
            "manager_name": "Manager",
            "hotel_phone_number": "1234567890",
            "hotel_website": "http://samplehotel.com",
            "number_of_rooms": 50,
            "check_in_datetime": "2024-01-17T12:00:00Z",
            "check_out_datetime": "2024-01-18T12:00:00Z",
            "location": {"coordinates": [69.2075, 34.5553]},
            "nearby_popular_landmark": "Sample Landmark",
            "property_type": property_type.id,
            "room_types": [room_type.id],
            "cancellation_days": 3,
            "cancellation_policy": "Flexible cancellation policy",
            "pet_friendly": True,
            "breakfast_included": True,
            "is_cancellation": True,
            "status": True,
            "is_online": True
        }
        response_create = self.create_property(create_data)
        self.assertEqual(response_create.status_code, status.HTTP_200_OK)

        property_instance = Property.objects.get(id=response_create.json().get('data').get('id'))

        response_retrieve = self.retrieve_property(property_instance)
        self.assertEqual(response_retrieve.status_code, status.HTTP_200_OK)

        updated_data = {
            "hotel_nick_name": "Updated Name"
        }
        response_update = self.update_property(property_instance, updated_data)
        print(response_update)
        self.assertEqual(response_update.status_code, status.HTTP_200_OK)

        response_list = self.list_property()
        self.assertEqual(response_list.status_code, status.HTTP_200_OK)

        response_exception_update = self.update_exception_property(999, updated_data)
        self.assertEqual(response_exception_update.status_code, status.HTTP_400_BAD_REQUEST)

        updated_exception_data = {
            "property_type": 10
        }
        response_exception_update = self.update_exception_property(property_instance, updated_exception_data)
        self.assertEqual(response_exception_update.status_code, status.HTTP_404_NOT_FOUND)

        exception_data = create_data.pop("number_of_rooms")

        response_exception_create = self.create_property(exception_data)
        self.assertEqual(response_exception_create.status_code, status.HTTP_400_BAD_REQUEST)

        response_exception_retrieve = self.retrieve_exception_property(999)
        self.assertEqual(response_exception_retrieve.status_code, status.HTTP_400_BAD_REQUEST)


class RoomInventoryViewSetTest(BaseHotelViewTest):
    def create_room(self, data, property_instance):
        self.client.force_authenticate(user=self.hotel, token=self.token)
        return self.client.post(f'/hotel/roomInventories/?property_id={property_instance}', data, format='json')

    def retrieve_room(self, room_instance):
        self.client.force_authenticate(user=self.hotel, token=self.token)
        return self.client.get(f'/hotel/roomInventories/{room_instance.id}/', format='json')

    def retrieve_exception_room(self, room_instance):
        self.client.force_authenticate(user=self.hotel, token=self.token)
        return self.client.get(f'/hotel/roomInventories/{room_instance}/', format='json')

    def update_room(self, room_instance, data):
        self.client.force_authenticate(user=self.hotel, token=self.token)
        return self.client.patch(f'/hotel/roomInventories/{room_instance.id}/', data, format='json')

    def update_exception_room(self, room_instance, data):
        self.client.force_authenticate(user=self.hotel, token=self.token)
        return self.client.patch(f'/hotel/roomInventories/{room_instance}/', data, format='json')

    def list_room(self):
        self.client.force_authenticate(user=self.hotel, token=self.token)
        return self.client.get('/hotel/roomInventories/', format='json')

    def test_room_inventory(self):
        User.objects.create_superuser(username='admin', email='admin@example.com', password='password')
        property_type = PropertyType.objects.create(property_type='Hotel')
        room_type = RoomType.objects.create(room_type='Suite')
        bed_type = BedType.objects.create(bed_type='Queen')
        bathroom_type = BathroomType.objects.create(bathroom_type='Private')
        room_feature = RoomFeature.objects.create(room_feature='Balcony')
        common_ameninity = CommonAmenities.objects.create(common_ameninity='WiFi')
        property_instance = Property.objects.create(
            parent_hotel_group="Updated group",
            hotel_nick_name="Nick name",
            manager_name="Manager",
            hotel_phone_number="1234567890",
            number_of_rooms=50,
            # check_in_time="2024-01-17T12:00:00Z",
            # check_out_time="2024-01-18T12:00:00Z",
            hotel_website="http://samplehotel.com",
            location=Point(12.971598, 77.594562),
            nearby_popular_landmark="Sample Landmark",
            property_type_id=property_type.id,
            # cancellation_days=3,
            # cancellation_policy="cancellation_policy",
            pet_friendly=True,
            breakfast_included=True,
            is_cancellation=True,
            status=True,
            is_online=True,
            owner=self.hotel
        )
        property_instance.room_types.set([room_type.id])
        create_data = {
            "room_name": "Sample Room",
            "floor": 2,
            "room_view": "City View",
            "num_of_rooms": 5,
            "area_sqft": 300.5,
            "room_type": room_type.id,
            "bed_type": [bed_type.id],
            "bathroom_type": bathroom_type.id,
            "room_features": [room_feature.id],
            "common_amenities": [common_ameninity.id],
            "is_updated_period": False,
            "adult_capacity": 2,
            "children_capacity": 1,
            "default_price": 100,
            "min_price": 80,
            "max_price": 120,
            "status": True,
            "images": [
                "owner/105/hotel_image/1000000195.jpg_1708495133",
                "owner/105/hotel_image/21cb4c4f-d806-4117-9922-b4e3ced215f1_1708498272",
                "owner/105/hotel_image/08e3c85e-6690-4d59-b4c4-d7bb8f97ec1b_1708495028",
                "owner/105/hotel_image/1000000183.jpg_1708495160"
            ],
            "check_in_time": "2024-01-17T12:00:00Z",
            "check_out_time": "2024-01-18T12:00:00Z"
        }

        response_create = self.create_room(create_data, property_instance.id)
        self.assertEqual(response_create.status_code, status.HTTP_200_OK)

        room_instance = RoomInventory.objects.get(id=response_create.json().get('data').get('id'))

        response_retrieve = self.retrieve_room(room_instance)
        if response_retrieve is not None:
            self.assertEqual(response_retrieve.status_code, status.HTTP_200_OK)
        else:
            # Handle the case where the response is None
            print("The response is None. Unable to perform assertions.")
        updated_data = {
            "room_name": "Updated Name"
        }
        response_update = self.update_room(room_instance, updated_data)
        self.assertEqual(response_update.status_code, status.HTTP_200_OK)

        response_list = self.list_room()
        self.assertEqual(response_list.status_code, status.HTTP_200_OK)

        response_exception_update = self.update_exception_room(999, updated_data)
        self.assertEqual(response_exception_update.status_code, status.HTTP_400_BAD_REQUEST)

        updated_exception_data = {
            "property_type": 10
        }
        response_exception_update = self.update_exception_room(room_instance, updated_exception_data)
        self.assertEqual(response_exception_update.status_code, status.HTTP_400_BAD_REQUEST)

        exception_data = create_data.pop("room_type")

        response_exception_create = self.create_room(exception_data, property_instance.id)
        self.assertEqual(response_exception_create.status_code, status.HTTP_400_BAD_REQUEST)

        response_exception_retrieve = self.retrieve_exception_room(999)
        self.assertEqual(response_exception_retrieve.status_code, status.HTTP_400_BAD_REQUEST)


class AccountListViewTest(BaseHotelViewTest):
    def get_account_list(self):
        self.client.force_authenticate(user=self.hotel, token=self.token)
        return self.client.get('/hotel/getAccountList/', format='json')

    def get_account_data_1(self):
        # Helper method to get the first account data
        return {
            "hotel_owner": self.hotel,
            "email": "test1@example.com",
            "phone": "1234567890",
            "contact_name": "John Doe",
            "type": "type",
            "account_id": "1234567890",
            "legal_business_name": "Test Business 1",
            "business_type": "Test Type 1",
            "status": True
        }

    def test_get_account_list_successful(self):
        # Create OwnerBankingDetail instances
        OwnerBankingDetail.objects.create(**self.get_account_data_1())

        self.client.force_authenticate(user=self.hotel, token=self.token)
        response = self.client.get('/hotel/getAccount/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('data', response.data)
        self.assertEqual(len(response.data['data']), 2)

    def test_get_account_list_empty(self):
        response = self.get_account_list()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('data', response.data)
        self.assertEqual(len(response.data['data']), 0)


class BookingListViewTest(BaseHotelViewTest):
    def get_booking_history(self):
        self.client.force_authenticate(user=self.hotel, token=self.token)
        return self.client.get('/hotel/bookingHistory/', format='json')

    def test_booking_list_view(self):
        property_instance = self.create_property()
        customer_instance = self.create_customer()

        # Create a BookingHistory instance
        self.create_booking(property_instance, customer_instance)

        response = self.get_booking_history()
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TransactionListViewTest(BaseHotelViewTest):
    def make_transaction_list_request(self):
        self.client.force_authenticate(user=self.hotel, token=self.token)
        return self.client.get('/hotel/transactions/')

    def test_transaction_list_view_single_data(self):
        property_instance = self.create_property()
        customer_instance = self.create_customer()
        room_type = RoomType.objects.create(room_type='Suite')
        bed_type = BedType.objects.create(bed_type='Queen')
        bathroom_type = BathroomType.objects.create(bathroom_type='Private')
        room_feature = RoomFeature.objects.create(room_feature='Balcony')
        common_amenities = CommonAmenities.objects.create(common_ameninity='WiFi')
        # Create a RoomInventory instance related to the hotel owner
        room = RoomInventory.objects.create(
            property=property_instance,
            room_name="Sample Room",
            floor=2,
            room_view="City View",
            area_sqft=300.5,
            room_type=room_type,
            bathroom_type=bathroom_type,
            num_of_rooms=5,
            adult_capacity=2,
            children_capacity=1,
            default_price=100,
            min_price=80,
            max_price=120,
            status=True
        )
        room.bed_type.add(bed_type)
        room.bathroom_type = bathroom_type
        room.room_features.add(room_feature)
        room.common_amenities.add(common_amenities)

        BookingHistory.objects.create(
            property=property_instance,
            customer=customer_instance,
            num_of_rooms=2,
            rooms=room,
            order_id="123456",
            check_in_date=timezone.now(),
            check_out_date=timezone.now(),
            amount=200.0,
            currency="USD",
            is_cancel=False,
            book_status=True,
            created_at=timezone.now()
        )

        response = self.make_transaction_list_request()
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class SubscriptionPlanViewTest(BaseHotelViewTest):
    def make_subscription_plan_request(self):
        self.client.force_authenticate(user=self.hotel, token=self.token)
        return self.client.get('/hotel/subscriptionPlan/')

    def test_subscription_plan_view_single_data(self):
        SubscriptionPlan.objects.create(
            name='3 months plan',
            price=100,
            duration=3,
            description='3 months subscription plan'
        )
        response = self.make_subscription_plan_request()
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class SubscriptionViewTest(BaseHotelViewTest):
    def setUp(self):
        super().setUp()
        # Create a subscription plan
        self.plan = SubscriptionPlan.objects.create(
            name='3 months plan',
            price=100,
            duration=3,
            description='3 months subscription plan'
        )

    def make_subscription_request(self):
        self.client.force_authenticate(user=self.hotel, token=self.token)
        return self.client.get('/hotel/subscription/')

    def test_get_subscription_view(self):
        # Create a SubscriptionTransaction instance
        SubscriptionTransaction.objects.create(
            subscription_plan=self.plan,
            owner=self.hotel,
            razorpay_subscription_id='test_subscription_id',
            payment_status=True
        )
        response = self.make_subscription_request()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_post_subscription_view(self):
        # Make POST request to the subscription endpoint
        self.client.force_authenticate(user=self.hotel, token=self.token)
        response = self.client.post('/hotel/subscription/', {'subscription_plan': self.plan.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RatingsListViewTest(BaseHotelViewTest):
    def authenticate_and_get_ratings(self):
        self.client.force_authenticate(user=self.hotel, token=self.token)
        return self.client.get('/hotel/ratings/')

    def test_ratings_list_view(self):
        property_instance = self.create_property()
        customer_instance = self.create_customer()

        Ratings.objects.create(
            property=property_instance,
            customer=customer_instance,
            ratings=5,
            review="Excellent service!"
        )
        response = self.authenticate_and_get_ratings()
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class BookingRetrieveViewTest(BaseHotelViewTest):
    def get_booking(self, booking_id):
        self.client.force_authenticate(user=self.hotel, token=self.token)
        return self.client.get(f'/hotel/bookingRetrieve/{booking_id}/')

    def test_booking_retrieve_view(self):
        property_instance = self.create_property()
        customer_instance = self.create_customer()

        booking_history_instance = self.create_booking(property_instance, customer_instance)

        # Create a guest detail
        GuestDetail.objects.create(
            booking=booking_history_instance,
            no_of_adults=2,
            no_of_children=1,
            age_of_children="5,7",
        )
        response = self.get_booking(booking_history_instance.pk)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
