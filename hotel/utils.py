import jwt
from datetime import datetime, timedelta

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