from django.db import models
from adminapp.models import BaseModel,IUMaster
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.postgres.fields import JSONField,ArrayField
from django.contrib.auth.models import AbstractUser, Group, Permission

class CustomUser(AbstractUser,BaseModel):
    username = None
    mobile_number = models.CharField(max_length=32)
    USERNAME_FIELD = 'id'
    REQUIRED_FIELDS = []
    email=models.EmailField(unique=True)
    temp_code=models.CharField(max_length=10, null=True, blank=True)
    is_approval=models.BooleanField(default=False)
    last_login_role = models.CharField(max_length=30,blank=True,null=True)
    approved_by=models.CharField(max_length=10, null=True, blank=True)
    iu_id=models.ForeignKey(IUMaster,related_name='CustomUser_iu_id',on_delete=models.CASCADE)


    class Meta:
        unique_together = (('mobile_number', 'iu_id'),)
        db_table = 'customuser'
        ordering = ['created_at']
    
    def __str__(self):
        return self.mobile_number

class UserPersonalProfile(BaseModel):  
    """details of user"""
    firstname=models.CharField(max_length=30,null=True,blank=True)
    lastname=models.CharField(max_length=30,null=True,blank=True)
    user=models.ForeignKey(CustomUser,related_name='userdetails',on_delete=models.CASCADE)
    profilephoto=JSONField(null=True,blank=True,default=dict)
    gender=models.CharField(max_length=20,null=True,blank=True)
    age=models.IntegerField(blank=True,null=True)
    language=models.TextField(blank=True,null=True)
    primary_address=models.TextField(blank=True,null=True)
    secondary_address=models.TextField(blank=True,null=True)
    iu_id = models.ForeignKey(IUMaster, on_delete=models.CASCADE, related_name='user_personal_profile_iu')

    class Meta:
        db_table = 'user_profile_details'
        ordering = ['created_at']



class RoleMaster(BaseModel):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    iu_id=models.ForeignKey(IUMaster,on_delete=models.CASCADE)

    class Meta:
        db_table="role_master"
        ordering = ["created_at"]



class RoleMapping(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE,related_name='custom_user')
    role = models.ForeignKey(RoleMaster, on_delete=models.CASCADE,related_name='role_master')
    iu_id=models.ForeignKey(IUMaster,on_delete=models.CASCADE)

    class Meta:
        db_table="role_mapping"

class PublisherProfile(BaseModel):
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='publisher_user_id')
    description=models.TextField(blank=True,null=True)
    experience=models.TextField(blank=True,null=True)
    document=ArrayField(JSONField(),default=list,blank=True)
    website_link=models.TextField(blank=True,null=True)
    approved_status=models.CharField(default='pending',max_length=50)
    role_type=models.CharField(max_length=50,blank=True,null=True)
    reason=models.TextField(blank=True,null=True)
    is_rejected=models.BooleanField(default=False)
    iu_id=models.ForeignKey(IUMaster,related_name='publisher_iu',on_delete = models.CASCADE)

    class Meta:
        db_table='publisher_profile'
        ordering = ['created_at']

class ApprovedProfiles(BaseModel):
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='approvedprofiles_user_id')
    description=models.TextField(blank=True,null=True)
    experience=models.TextField(blank=True,null=True)
    document=ArrayField(JSONField(),default=list,blank=True)
    website_link=models.TextField(blank=True,null=True)
    is_approved=models.BooleanField(default=True)
    role_type=models.CharField(max_length=50,blank=True,null=True)
    iu_id=models.ForeignKey(IUMaster,related_name='approvedprofiles_iu',on_delete = models.CASCADE)

    class Meta:
        db_table='approved_profiles'
        ordering = ['created_at']