from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Owner, PropertyType, RoomFeature, RoomType, BathroomType, BedType, \
    CommonAmenities, Property, RoomInventory
from django.contrib.gis.geos import Point


class BaseHotelViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.hotel = Owner.objects.create(
            phone_number="1234567890",
            hotel_name="Hotel 1",
            address="This is address"
        )
        self.login_data = {
            'phone_number': '1234567890',
            'fcm_token': 'new_fcm',
        }
        self.token = None
        self.login_hotel()

    def login_hotel(self):
        response = self.client.post('/hotel/login/', self.login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.token = response.data['data'].get('token')


class HotelRegisterViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.valid_data = {
            "phone_number": "1234567890",
            "hotel_name": "Hotel 1",
            "address": "This is address"
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
        PropertyType.objects.create(property_type='Hotel', bid_time_duration=5)
        RoomType.objects.create(room_type='Suite')
        BedType.objects.create(bed_type='Queen')
        BathroomType.objects.create(bathroom_type='Private')
        RoomFeature.objects.create(room_feature='Balcony')
        CommonAmenities.objects.create(common_ameninity='WiFi')
        self.client.force_authenticate(user=self.hotel, token=self.token)
        response = self.client.get('/hotel/masterRetrieve/', format='json')
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
        property_type = PropertyType.objects.create(property_type='Hotel', bid_time_duration=5)
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
        self.assertEqual(response_update.status_code, status.HTTP_200_OK)

        response_list = self.list_property()
        self.assertEqual(response_list.status_code, status.HTTP_200_OK)

        response_exception_update = self.update_exception_property(999, updated_data)
        self.assertEqual(response_exception_update.status_code, status.HTTP_400_BAD_REQUEST)

        updated_exception_data = {
            "property_type": 10
        }
        response_exception_update = self.update_exception_property(property_instance, updated_exception_data)
        self.assertEqual(response_exception_update.status_code, status.HTTP_400_BAD_REQUEST)

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
        property_type = PropertyType.objects.create(property_type='Hotel', bid_time_duration=5)
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
            check_in_datetime="2024-01-17T12:00:00Z",
            check_out_datetime="2024-01-18T12:00:00Z",
            hotel_website="http://samplehotel.com",
            location=Point(12.971598, 77.594562),
            nearby_popular_landmark="Sample Landmark",
            property_type_id=property_type.id,
            cancellation_days=3,
            cancellation_policy="cancellation_policy",
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
            "area_sqft": 300.5,
            "room_type": room_type.id,
            "bed_type": bed_type.id,
            "bathroom_type": bathroom_type.id,
            "room_features": [room_feature.id],
            "common_amenities": [common_ameninity.id],
            "is_updated_period": False,
            "adult_capacity": 2,
            "children_capacity": 1,
            "default_price": 100,
            "min_price": 80,
            "max_price": 120,
            "status": True
        }

        response_create = self.create_room(create_data, property_instance.id)
        self.assertEqual(response_create.status_code, status.HTTP_200_OK)

        room_instance = RoomInventory.objects.get(id=response_create.json().get('data').get('id'))

        response_retrieve = self.retrieve_room(room_instance)
        self.assertEqual(response_retrieve.status_code, status.HTTP_200_OK)

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
