from rest_framework import serializers
from posts.models import *
from users.serializers import *
from rest_framework.permissions import IsAuthenticated


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
    likes_count=serializers.SerializerMethodField()
    comments_count=serializers.SerializerMethodField()
    shared_count=serializers.SerializerMethodField()
    is_liked=serializers.SerializerMethodField()
    class Meta:
        model = PostDetails
        fields = ['id', 'publisher', 'category', 'title', 'content', 'image', 'post_status','likes_count','comments_count','shared_count', 'user_profile','is_liked']

    def get_user_profile(self, obj):
        profile = obj.publisher.userdetails.first()
        role = self.context.get('role')
        if role in ['publisher','consumer']:
            return "Not applicable"
        if profile:
            return {'id': profile.id,'firstname': profile.firstname,'lastname': profile.lastname,'mobile_number':profile.user.mobile_number,'email':profile.user.email}
        return None
    
    def get_likes_count(self,obj):
        likes=obj.likes_users_list.count()
     
        if likes:
            return likes
        return 0

    def get_is_liked(self, obj):
        # Access the current user from the context
        user = self.context.get('request').user
        role = self.context.get('role')
        if role in ['publisher']:
            return "N/A"
        if user.is_authenticated:
            return obj.likes_users_list.filter(id=user.id).exists()
        return False

    def get_comments_count(self,obj):
        comments_detail=Comments.objects.filter(post=obj,iu_id=obj.iu_id,is_active=True,is_removed_comment=False)
        return comments_detail.count()
    
    def get_shared_count(self,obj):
        shares=obj.shared_users_list.count()
        if shares:
            return shares
        return 0

class SubcommentSerializer(serializers.ModelSerializer):
    class Meta:
        model=Comments
        fields=['id','message']

class CommentsSerializer(serializers.ModelSerializer):
    subcomments=serializers.SerializerMethodField()
    class Meta:
        model=Comments
        fields=['id','message','subcomments']

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super(CommentsSerializer, self).__init__(*args, **kwargs)
 
        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)
    
    def get_subcomments(self,obj):
        subcomments = Comments.objects.filter(parent_comment=obj, is_active=True)
        print(subcomments)
        data=SubcommentSerializer(subcomments, many=True, context=self.context).data
        return data