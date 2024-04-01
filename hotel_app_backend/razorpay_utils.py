import razorpay
from django.conf import settings
import requests


razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_API_KEY, settings.RAZORPAY_API_SECRET))

headers = {
    'Content-Type': 'application/json',
    'Authorization': settings.RAZORPAY_AUTH_TOKEN
}


def razorpay_request(endpoint, method, data):
    url = settings.RAZORPAY_BASE_URL + endpoint
    response = requests.request(method, url, headers=headers, json=data)
    return response
