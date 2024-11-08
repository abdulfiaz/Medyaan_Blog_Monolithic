from rest_framework import serializers
from posts.models import PostCategory,PostDetails
from users.serializers import *

class PostCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = PostCategory
        fields = '__all__'

class GetPostCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = PostCategory
        fields = ['id','category_name','description','is_archived','iu_id']

class PostDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostDetails
        fields = '__all__'

class GetPostDetailsSerializer(serializers.ModelSerializer):
    user_profile = serializers.SerializerMethodField()

    class Meta:
        model = PostDetails
        fields = ['id', 'publisher', 'category', 'title', 'content', 'image', 'post_status', 'user_profile']

    def get_user_profile(self, obj):
        profile = obj.publisher.userdetails.first()

        if profile:
            return {'id': profile.id,'firstname': profile.firstname,'lastname': profile.lastname,'mobile_number':profile.user.mobile_number,'email':profile.user.email}
        return None
