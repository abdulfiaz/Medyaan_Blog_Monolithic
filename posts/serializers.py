from rest_framework import serializers
from posts.models import PostCategory

class PostCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = PostCategory
        fields = '__all__'

class GetPostCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = PostCategory
        fields = ['id','category_name','description','is_archived','iu_id']