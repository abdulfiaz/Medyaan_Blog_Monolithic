from django.db import models
from adminapp.models import BaseModel,IUMaster


class PostCategory(BaseModel):
    category_name = models.CharField(max_length=50)
    description = models.CharField(max_length=100,null=True,blank=True)
    is_archived = models.BooleanField(default=False)
    iu_id = models.ForeignKey(IUMaster,related_name='postcategory_iu',on_delete = models.CASCADE)

    class Meta:
        db_table = 'PostCategory'
        ordering = ['created_at']