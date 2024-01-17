import jwt
from datetime import datetime, timedelta


def generate_token(id):
    payload = {
        'user_id': id,
        'exp': datetime.utcnow() + timedelta(days=1)
    }
    jwt_token = jwt.encode(payload, 'secret', algorithm='HS256')
    return jwt_token
