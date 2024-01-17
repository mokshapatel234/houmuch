import jwt
from datetime import datetime, timedelta
from rest_framework.response import Response

def generate_token(id):
    payload = {
        'user_id': id
,
        'exp': datetime.utcnow() + timedelta(days=1)  
    }

    jwt_token = jwt.encode(payload, 'secret', algorithm='HS256')

    return jwt_token

def model_name_to_snake_case(name):
    return ''.join(['_' + i.lower() if i.isupper() else i for i in name]).lstrip('_')

def generate_response(instance, message, status_code, serializer_class):
    serializer = serializer_class(instance)
    response_data = {
        'result': True,
        'data': serializer.data,
        'message': message,
    }
    return Response(response_data, status=status_code)