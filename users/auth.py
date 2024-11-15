from django.conf import settings
import jwt
import boto3
from django.utils import timezone
from botocore.config import Config
 
#To get the multiple roles for the user from token
def get_user_roles(request):
    roles = None 
    authorization_header = request.META.get('HTTP_AUTHORIZATION', None)
    if authorization_header:
        token = authorization_header.split(' ')[1]
        decoded_data = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        roles = decoded_data.get('user_role')
    return roles

def upload_image_s3(image_file, file_name):
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_S3_REGION_NAME,
            config=Config(signature_version='s3v4')
        )
        
        # Generate unique filename with timestamp
        current_time = timezone.now().strftime('%Y-%m-%d_%H:%M:%S')
        file_extension = file_name.split('.')[-1]
        unique_filename = f"{file_name.split('.')[0]}_{current_time}.{file_extension}"
        
        # Upload the file to S3
        s3_client.upload_fileobj(
            image_file,
            settings.AWS_STORAGE_BUCKET_NAME,
            f"posts_images/{unique_filename}",
            ExtraArgs={'ACL': 'public-read', 'ServerSideEncryption': 'AES256'}
        )
        
        # Generate the image URL
        image_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/posts_images/{unique_filename}"
        return image_url
    except Exception as e:
        raise Exception(f"Image upload failed: {str(e)}")
