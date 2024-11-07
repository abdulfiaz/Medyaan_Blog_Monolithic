from rest_framework import serializers
from users.models import CustomUser, UserPersonalProfile, RoleMaster,PublisherProfile
from adminapp.models import IUMaster
from django.contrib.auth.hashers import make_password,check_password


class CustomUserSerializer(serializers.ModelSerializer):
    confirm_password = serializers.CharField(write_only=True) 
    class Meta:
        model = CustomUser
        fields = ['mobile_number', 'email','password','temp_code', 'is_approval', 'approved_by', 'iu_id','created_by','modified_by','confirm_password','is_active']
    
    def validate(self, data):
        if 'password' in data:
            if data['password'] != data.pop('confirm_password'):
                raise serializers.ValidationError('Passwords do not match')
            data['password'] = make_password(data['password'])  

        return data
    
class UserPersonalProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPersonalProfile
        fields = '__all__'

class GetCustomUserSerializer(serializers.ModelSerializer):
    firstname = serializers.CharField(source='userdetails.first.firstname', default=None)
    lastname = serializers.CharField(source='userdetails.first.lastname', default=None)
    profilephoto = serializers.CharField(source='userdetails.first.profilephoto', default={})
    gender = serializers.CharField(source='userdetails.first.gender', default=None)
    age = serializers.IntegerField(source='userdetails.first.age', default=None)
    language = serializers.CharField(source='userdetails.first.language', default=None)
    primary_address = serializers.CharField(source='userdetails.first.primary_address', default=None)
    secondary_address = serializers.CharField(source='userdetails.first.secondary_address', default=None)

    class Meta:
        model = CustomUser
        fields = ['mobile_number', 'email', 'firstname', 'lastname','profilephoto', 'gender', 'age', 'language','primary_address', 'secondary_address']

class PublisherProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model=PublisherProfile
        fields='__all__'

class GetPublisherProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model=PublisherProfile
        fields=['id','role_type','description','experience','document','approved_status','reason']