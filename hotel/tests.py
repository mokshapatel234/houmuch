from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Owner, PropertyType, RoomFeature, RoomType, BathroomType, BedType, CommonAmenities


class HotelRegisterViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.valid_data = {
            "phone_number":"1234567890",
            "hotel_name":"Hotel 1",
            "address":"This is address"
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


class hotelLoginViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.hotel = Owner.objects.create(
            phone_number = "1234567890",
            hotel_name = "Hotel 1",
            address = "This is address"
        )
        self.login_data = {
            'phone_number': '1234567890',
            'fcm_token': 'new_fcm',
        }

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


class HotelOwnerProfileViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.hotel = Owner.objects.create(
            phone_number = "1234567890",
            hotel_name = "Hotel 1",
            address = "This is address"
        )
        self.login_data = {
            'phone_number': '1234567890',
            'fcm_token': 'new_fcm',
        }
        self.token = None

    def test_hotel_login_success(self):
        response = self.client.post('/hotel/login/', self.login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.token = response.data['data'].get('token')

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


class MasterRetrieveViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.hotel = Owner.objects.create(
            phone_number = "1234567890",
            hotel_name = "Hotel 1",
            address = "This is address"
        )
        self.login_data = {
            'phone_number': '1234567890',
            'fcm_token': 'new_fcm',
        }
        self.token = None

    def test_hotel_login_success(self):
        response = self.client.post('/hotel/login/', self.login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.token = response.data['data'].get('token')

    def test_master_retrieve_view(self):
        property_type = PropertyType.objects.create(property_type='Hotel', bid_time_duration=5)
        room_type = RoomType.objects.create(room_type='Suite')
        bed_type = BedType.objects.create(bed_type='Queen')
        bathroom_type = BathroomType.objects.create(bathroom_type='Private')
        room_feature = RoomFeature.objects.create(room_feature='Balcony')
        common_amenities = CommonAmenities.objects.create(common_ameninity='WiFi')
        self.client.force_authenticate(user=self.hotel, token=self.token)
        response = self.client.get('/hotel/masterRetrieve/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)