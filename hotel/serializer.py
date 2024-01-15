from rest_framework import serializers 
from .models import Owner


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Owner
        fields = '__all__'

    is_verified = serializers.CharField(required=False)
    is_active = serializers.CharField(required=False)
    bidding_mode = serializers.CharField(required=False)


class LoginSerializer(serializers.ModelSerializer):
    class Meta:
        model=Owner
        fields = ('phone_number',)


class OwnerProfileSerializer(serializers.ModelSerializer):
   
    class Meta:
        model = Owner
        fields = ('first_name', 'last_name', 'email', 'profile_image', 'address', 'phone_number', 'bidding_mode', 'government_id')
        extra_kwargs = {"government_id": {"required": False, "read_only": True}}
