from datetime import datetime
from rest_framework.decorators import api_view
from django.conf import settings
import boto3
from hotel.authentication import JWTAuthentication as JWTAuthenticationForOwner
from customer.authentication import JWTAuthentication as JWTAuthenticationForCustomer
from rest_framework import exceptions, status
from hotel.utils import generate_response, error_response
from .messages import EXCEPTION_MESSAGE, DATA_CREATE_MESSAGE, FAILED_PRESIGNED_RESPONSE


s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name='ap-south-1'
)


def get_presigned_key(filename, user_type, image_type, user_id):
    key = int(datetime.timestamp(datetime.now()))
    if user_type == 'owner':
        if image_type == 'profile':
            return f"owner/{user_id}/profile_image/{filename}_{key}"
        elif image_type == 'hotel':
            return f"owner/{user_id}/hotel_image/{filename}_{key}"
    elif user_type == 'customer':
        if image_type == 'profile':
            return f"customer/{user_id}/profile_image/{filename}_{key}"
    raise error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def get_presigned_url(request):
    try:
        data = request.data.get('data', [])
        presigned_urls = []
        for item in data:
            file_name = item.get('file_name')
            image_type = item.get('image_type')
            user_type = item.get('user_type')
            if user_type == 'owner':
                authentication_class = JWTAuthenticationForOwner()
            elif user_type == 'customer':
                authentication_class = JWTAuthenticationForCustomer()
            else:
                raise exceptions.AuthenticationFailed('Invalid user_type')
            auth_result = authentication_class.authenticate(request)
            user_id = auth_result[0].id
            key = get_presigned_key(file_name, user_type, image_type, user_id)
            try:
                response = s3_client.generate_presigned_post(
                    Bucket=settings.AWS_STORAGE_BUCKET_NAME, Key=key, ExpiresIn=500
                )
                presigned_urls.append(response)
            except Exception:
                raise error_response(FAILED_PRESIGNED_RESPONSE, status.HTTP_400_BAD_REQUEST)
        return generate_response(presigned_urls, DATA_CREATE_MESSAGE, status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return error_response(EXCEPTION_MESSAGE, status.HTTP_400_BAD_REQUEST)
