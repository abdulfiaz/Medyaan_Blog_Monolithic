from django.db import models
from adminapp.models import BaseModel,IUMaster
from django.db import models
from users.models import CustomUser
from django.contrib.postgres.fields import ArrayField,JSONField


class PostCategory(BaseModel):
    category_name = models.CharField(max_length=50)
    description = models.CharField(max_length=100,null=True,blank=True)
    is_archived = models.BooleanField(default=False)
    iu_id = models.ForeignKey(IUMaster,related_name='postcategory_iu',on_delete = models.CASCADE)

    class Meta:
        db_table = 'PostCategory'
        ordering = ['created_at']

class PostDetails(BaseModel):
    publisher=models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='post_publisher_id')
    likes_users_list=models.ManyToManyField(CustomUser,related_name='post_liked_users',blank=True)
    viewed_users_list=models.ManyToManyField(CustomUser,related_name='post_viewed_users',blank=True)
    shared_users_list=models.ManyToManyField(CustomUser,related_name='post_shared_users',blank=True)
    comments_users_list=models.ManyToManyField(CustomUser,related_name='post_comments_users',blank=True)
    category=models.ForeignKey(PostCategory,on_delete=models.CASCADE,blank=True,null=True,related_name='post_category')
    title=models.TextField(blank=True,null=True)
    content=models.TextField(blank=True,null=True)
    status=models.CharField(default='pending',max_length=50)
    image=ArrayField(JSONField(),default=list,blank=True)
    is_archived=models.BooleanField(default=False)
    iu_id=models.ForeignKey(IUMaster,related_name='postdetails_iu',on_delete = models.CASCADE)

    class Meta:
        db_table='post_details'
        ordering = ['created_at']        

class Comments(BaseModel):
    parent_comment=models.ForeignKey('self',on_delete=models.CASCADE,blank=True,null=True,related_name='parent_comments_id')
    post=models.ForeignKey(PostDetails,on_delete=models.CASCADE,related_name='comments_post_id')
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='comments_user_id')
    sub_comment=models.BooleanField(default=False)
    list_tag_user=ArrayField(models.IntegerField(blank=True,null=True))
    message=models.TextField(blank=True,null=True)
    is_removed_comment=models.BooleanField(default=False)
    timestamp=models.IntegerField()
    iu_id=models.ForeignKey(IUMaster,related_name='comments_iu',on_delete = models.CASCADE)

    class Meta:
        db_table='comments'
        ordering = ['created_at'] 