from rest_framework import serializers 
from django.core.validators import RegexValidator
from django.conf import settings
from .models import Hotel

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hotel
        fields = '__all__'
    
    # Override the default behavior of the fields
    # first_name = serializers.CharField(required=True)
    # last_name = serializers.CharField(required=True)
    # phone_number = serializers.CharField(required=True)
    email = serializers.EmailField(required=False)
    address = serializers.CharField(required=False)
    government_id = serializers.CharField(required=False)
    is_verified = serializers.CharField(required=False)
    is_active = serializers.CharField(required=False)
    bidding_mode = serializers.CharField(required=False)

class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model=Hotel
        fields = ('phone_number',)