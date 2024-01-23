from rest_framework.test import APITestCase
from rest_framework import status
from .models import Customer


class CustomerRegisterViewTest(APITestCase):
    def setUp(self):
        self.client = Customer()

    def test_customer_registration(self):
        data = {
            'phone_number': '1234567890',
            'fcm_token': 'fcm_token',
            'device_id': 'device_id'
        }

        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
