import jwt
import uuid
from datetime import datetime
from calendar import timegm

from django.conf import settings
from rest_framework_jwt.settings import api_settings
from users.models import RoleMapping

def jwt_get_secret_key():
    
    return settings.SECRET_KEY

def jwt_payload_handler(user):

    """
    Custom Payload Handler.
    """

    if user.last_login_role is None:
        rolemapping = RoleMapping.objects.filter(user=user).order_by('role_id').first()
        role_name = rolemapping.role.name
    else:
        role_name = user.last_login_role

    payload = {
        'user_id': user.pk,
        'email': user.email,
        'user_role' : role_name,
        'exp': datetime.utcnow() + api_settings.JWT_EXPIRATION_DELTA
    }

    # Include original issued at time for a brand new token,
    # to allow token refresh
    if api_settings.JWT_ALLOW_REFRESH:

        payload['orig_iat'] = timegm(
            datetime.utcnow().utctimetuple()
        )

    if api_settings.JWT_AUDIENCE is not None:
        payload['aud'] = api_settings.JWT_AUDIENCE

    if api_settings.JWT_ISSUER is not None:
        payload['iss'] = api_settings.JWT_ISSUER

    return payload


def jwt_get_userid_from_payload_handler(payload):
    """
    This function is overridden to provide custom userid field for token authentication

    Refer authentication in 
    rest_framework_jwt/authentication.py
    """

    try:
        return payload.get('user_id')
    except:
        return None

def jwt_encode_handler(payload):
    key = jwt_get_secret_key()
    return jwt.encode(
        payload,
        key,
        api_settings.JWT_ALGORITHM
    ).decode('utf-8')

def jwt_decode_handler(token):
    key = jwt_get_secret_key()

    try:
        return jwt.decode(
            token,
            key,
            algorithms=[api_settings.JWT_ALGORITHM]
        )
    except Exception as e:
        return None