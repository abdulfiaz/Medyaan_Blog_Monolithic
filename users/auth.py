from django.conf import settings
import jwt
 
#To get the multiple roles for the user from token
def get_user_roles(request):
    authorization_header = request.META.get('HTTP_AUTHORIZATION', None)
    if authorization_header:
        token = authorization_header.split(' ')[1]
        decoded_data = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        roles = decoded_data.get('user_role')
    return roles