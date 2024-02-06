from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Customer


class BaseCustomerViewTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer_data = {
            'phone_number': '1234567890',
            'device_id': 'device_id',
            'fcm_token': 'new_fcm',
        }
        self.customer = Customer.objects.create(
            phone_number=self.customer_data['phone_number'],
            first_name='Customer1',
            last_name='Name',
            fcm_token=self.customer_data['fcm_token'],
            device_id=self.customer_data['device_id']
        )
        self.token = None
        self.login_customer()

    def login_customer(self):
        response = self.client.post('/customer/login/', self.customer_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.token = response.data['data'].get('token')


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
