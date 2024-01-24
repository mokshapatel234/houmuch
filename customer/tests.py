from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Customer


class CustomerRegisterViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.valid_data = {
            "phone_number": "4569871230",
            "first_name": "Customer1",
            "last_name": "Name",
            "fcm_token": "new_fcm",
            "device_id": "device_id"
        }

    def register_customer(self, data):
        return self.client.post('/customer/register/', data, format='json')

    def test_valid_customer_registration(self):
        response = self.register_customer(self.valid_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_invalid_customer_registration(self):
        invalid_data = {
            "phone_number": "4569871230",
            "first_name": "Customer1"
        }
        response = self.register_customer(invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CustomerLoginViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = Customer.objects.create(
            phone_number='1234567890',
            first_name='Customer1',
            last_name='Name',
            fcm_token='fcm_token',
            device_id='device_id'
        )
        self.login_data = {
            'phone_number': '1234567890',
            'device_id': 'device_id',
            'fcm_token': 'new_fcm',
        }

    def test_customer_login_success(self):
        response = self.client.post('/customer/login/', self.login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_customer_login_failure_not_registered(self):
        invalid_data = {'phone_number': '9876543210', 'device_id': 'device_id', 'fcm_token': 'new_fcm'}
        response = self.client.post('/customer/login/', invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_customer_login_failure_missing_device_id(self):
        invalid_data = {'phone_number': '1234567890', 'fcm_token': 'new_fcm'}
        response = self.client.post('/customer/login/', invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CustomerProfileViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = Customer.objects.create(
            phone_number='1234567890',
            first_name='Customer1',
            last_name='Name',
            fcm_token='fcm_token',
            device_id='device_id'
        )
        self.login_data = {
            'phone_number': '1234567890',
            'device_id': 'device_id',
            'fcm_token': 'new_fcm',
        }
        self.token = None

    def test_customer_login_success(self):
        response = self.client.post('/customer/login/', self.login_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.token = response.data['data'].get('token')

    def test_customer_profile_view_get(self):
        self.client.force_authenticate(user=self.customer, token=self.token)
        response = self.client.get('/customer/profile/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_customer_profile_view_patch(self):
        self.client.force_authenticate(user=self.customer, token=self.token)
        update_data = {'first_name': 'Updated', 'last_name': 'Name'}
        response = self.client.patch('/customer/profile/', update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
