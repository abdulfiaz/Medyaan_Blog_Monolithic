from django.shortcuts import render
from rest_framework.views import APIView,status
from rest_framework.response import Response
from posts.serializers import *
from posts.models import *
from users.models import *
from users.auth import get_user_roles
from django.conf import settings
from adminapp.iudetail import get_iuobj    
from django.db import transaction
from django.utils import timezone


# category view for posts i.e sports,education...
class PostCategoryView(APIView):
    def get(self,request):
        category_id = request.query_params.get('category_id',None)
        user_role = get_user_roles(request)
        if user_role != 'admin':
            return Response({"status":"error","message":"You are unauthorized to do this action !"},status=status.HTTP_401_UNAUTHORIZED)
        
        if category_id:
            try:
                category_obj=PostCategory.objects.get(id=category_id,is_active=True)
            except PostCategory.DoesNotExist:
                return Response({"status":"error","message":"Category not found !"},status=status.HTTP_404_NOT_FOUND)
            serializer = GetPostCategorySerializer(category_obj)

        else:
            category_obj = PostCategory.objects.filter(is_active=True)
            serializer = GetPostCategorySerializer(category_obj,many=True)

        return Response({"status":"success","message":"Category retrievd successfully!","data":serializer.data},status=status.HTTP_200_OK)

    def post(self,request):
        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
        iu_master = get_iuobj(domain)
        if not iu_master :
            return Response({"status":"error","message":"IU not found"},status=status.HTTP_404_NOT_FOUND)
        
        user_role = get_user_roles(request)
        
        if user_role != 'admin':
            return Response({"status":"error","message":"You are unauthorized to do this action !"},status=status.HTTP_401_UNAUTHORIZED)
        
        transaction.set_autocommit(False)
        data=request.data
        data['iu_id']=iu_master.id
        data['created_by']=request.user.id

        serializer = PostCategorySerializer(data=data)

        if not serializer.is_valid():
            transaction.rollback()
            return Response({"status":"error","message":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        transaction.commit()
        return Response({"status":"success","message":"Category Created Successfully !"},status=status.HTTP_201_CREATED)
    
    def put(self,request):
        category_id = request.data.get('category_id')
        user_role = get_user_roles(request)

        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
        iu_master = get_iuobj(domain)
        if not iu_master :
            return Response({"status":"error","message":"IU not found"},status=status.HTTP_404_NOT_FOUND)

        if user_role != 'admin':
            return Response({"status":"error","message":"You are unauthorized to do this action !"},status=status.HTTP_401_UNAUTHORIZED)
        
        if not category_id:
            return Response({"status":"error","message":"category_id is required"},status=status.HTTP_400_BAD_REQUEST)
        
        try:
            category_obj = PostCategory.objects.get(id=category_id,is_active=True,iu_id=iu_master)
        except PostCategory.DoesNotExist:
            return Response({"staus":"error","message":"Category not found !"},status=status.HTTP_404_NOT_FOUND)
        
        transaction.set_autocommit(False)
        data=request.data
        data['modified_by']=request.user.id

        serializer = PostCategorySerializer(category_obj,data=data,partial=True)

        if not serializer.is_valid():
            transaction.rollback()
            return Response({"status":"error","message":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        transaction.commit()
        return Response({"status":"success","message":"Category Updated Successfully !"},status=status.HTTP_201_CREATED)
    
    def delete(self,request):
        try:
            category_id = request.data.get("category_id")
            user_role = get_user_roles(request)

            domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
            iu_master = get_iuobj(domain)
            if not iu_master :
                return Response({"status":"error","message":"IU not found"},status=status.HTTP_404_NOT_FOUND)

            if user_role != 'admin':
                return Response({"status":"error","message":"You are unauthorized to do this action !"},status=status.HTTP_401_UNAUTHORIZED)
            
            if not category_id:
                return Response({"status":"error","message":"category_id is required"},status=status.HTTP_403_FORBIDDEN)
            
            try:
                category_obj = PostCategory.objects.get(id=category_id,is_active=True,iu_id=iu_master)
            except PostCategory.DoesNotExist:
                return Response({"status":"error","message":"Category not found !"},status=status.HTTP_404_NOT_FOUND)
            
            category_obj.is_active=False
            category_obj.is_archived=True
            category_obj.save()

            return Response({"status":"success","message":"category deleted successfully !"},status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_403_FORBIDDEN)

class PostDetailsView(APIView):
    def get(self,request):
        try:
            category_id=request.query_params.get('category_id',None)
            publisher_user_id=request.query_params.get('user_id',None)
            domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
            iu_master = get_iuobj(domain)
            if not iu_master :
                return Response({"status":"error","message":"UNAUTHORIZED DOMAIN"},status=status.HTTP_404_NOT_FOUND)
            if publisher_user_id:
                publisher_detail=CustomUser.objects.get(id=publisher_user_id,is_active=True,iu_id=iu_master)
                publish_user=PublisherProfile.objects.get(user=publisher_detail,is_active=True,iu_id=iu_master,approved_status='approved',role_type='publisher')
                post=PostDetails.objects.filter(publisher=publish_user.user,iu_id=iu_master,is_active=True,is_archived=False,post_status='published').order_by('-created_at')
            elif category_id:
                post=PostDetails.objects.filter(category_id=category_id,iu_id=iu_master,is_active=True,is_archived=False,post_status='published').order_by('-created_at')
            else:
                post=PostDetails.objects.filter(iu_id=iu_master,is_active=True,is_archived=False,post_status='published').order_by('-created_at')

            serializer=GetPostDetailsSerializer(post,many=True)
            return Response({"status":"success","message":"Post Details","data":serializer.data},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_400_BAD_REQUEST)
        
    def post(self,request):
        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
        iu_master = get_iuobj(domain)
        if not iu_master :
            return Response({"status":"error","message":"Unauthorized domain"},status=status.HTTP_401_UNAUTHORIZED)        

        user_role = get_user_roles(request)

        if user_role != 'publisher':
            return Response({"status":"error","message":"You are unauthorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)
        
        publisher_status = PublisherProfile.objects.get(user=request.user,is_active=True,role_type='publisher',is_rejected=False)
        if publisher_status.approved_status == 'pending':
            return Response({"status":"error","message":"You are unauthorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)
        
        transaction.set_autocommit(False)
        data=request.data
        data['created_by']=request.user.id
        data['publisher']=request.user.id
        data['iu_id']=iu_master.id
        
        serializer = PostDetailsSerializer(data=data)

        if not serializer.is_valid():
            transaction.rollback()
            return Response({"status":"error","message":serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        transaction.commit()
        return Response({"status":"success","message":"Post created successfully!",'data':serializer.data},status=status.HTTP_201_CREATED)
    
    def put(self,request):
        post_id = request.data.get('post_id')

        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
        iu_master = get_iuobj(domain)
        if not iu_master :
            return Response({"status":"error","message":"Unauthorized domain"},status=status.HTTP_401_UNAUTHORIZED)
        
        if not post_id:
            return Response({"status":"error","message":"post_id is required"},status=status.HTTP_400_BAD_REQUEST)
        
        try:
            post_obj=PostDetails.objects.get(id=post_id,publisher=request.user.id,post_status='published',is_active=True,iu_id=iu_master)
        except PostDetails.DoesNotExist:
            return Response({"status":"error","message":"Post not found!"},status=status.HTTP_404_NOT_FOUND)
        
        data =request.data
        data['modified_by']=request.user.id
        data['post_status']='pending'

        serializer = PostDetailsSerializer(post_obj,data=data,partial=True)

        if not serializer.is_valid():
            transaction.rollback()
            return Response({"status":"error","message":serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        transaction.commit()
        return Response({"status":"success","message":"Post updated successfully!"},status=status.HTTP_201_CREATED)
        
    def delete(self,request):
        try:
            post_id = request.data.get('post_id')
            domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
            iu_master = get_iuobj(domain)
            if not iu_master :
                return Response({"status":"error","message":"Unauthorized domain"},status=status.HTTP_401_UNAUTHORIZED)        

            user_role = get_user_roles(request)
            try:
                if user_role == 'manager':
                    post_obj = PostDetails.objects.get(id=post_id,post_status='published',is_active=True,iu_id=iu_master)
                elif user_role == 'publisher':
                    post_obj = PostDetails.objects.get(id=post_id,post_status='published',is_active=True,publisher=request.user.id,iu_id=iu_master)
            except PostDetails.DoesNotExist:
                return Response({"status":"error","message":"post not found"},status=status.HTTP_404_NOT_FOUND)
            
            post_obj.is_active=False
            post_obj.is_archived=True
            post_obj.modified_by=request.user.id
            post_obj.save()

            return Response({"status":"success","message":"post deleted successfully !"},status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_403_FORBIDDEN)

class PostApprovalView(APIView):
    def get(self,request):
        approved_status = request.query_params.get('status','pending')
        user_role = get_user_roles(request)
        
        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
        iu_master = get_iuobj(domain)
        if not iu_master:
            return Response({'status': 'failure', 'message': 'Unauthorized domain'},status=status.HTTP_404_NOT_FOUND)

        if user_role != 'manager':
            return Response({"status":"error","message":"You are unaithorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)
        
        # to count the total of aproved_status'pending,approved,rejected' and total of all publisher,eventorganiser
        
        counts = {}
        all_data = PostDetails.objects.filter(iu_id=iu_master, is_active=True)
        posts = all_data.filter(post_status=approved_status)

        counts['total_posts'] = all_data.count()
        approved_statuses = ['pending', 'published', 'rejected']
        for post_status in approved_statuses:
            counts[f'status_{post_status}'] = all_data.filter(post_status=post_status).count()
    

        posts_data = GetPostDetailsSerializer(posts, many=True)
        return Response({"status":"success","message":"data retrieved successfully","data": posts_data.data,"counts": counts}, status=status.HTTP_200_OK)

    def put(self,request):
        post_id = request.data.get("post_id")
        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
        iu_master = get_iuobj(domain)
        if not iu_master :
            return Response({"status":"error","message":"Unauthorized domain"},status=status.HTTP_401_UNAUTHORIZED)
        
        user_role = get_user_roles(request)

        if user_role != 'manager':
            return Response({"status":"error","message":"You are unauthorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            post_obj=PostDetails.objects.get(id=post_id,post_status='pending',is_active=True,iu_id=iu_master)
        except PostDetails.DoesNotExist:
            return Response({"status":"error","message":"Post not found"},status=status.HTTP_404_NOT_FOUND)
        
        transaction.set_autocommit(False)
        data=request.data
        data['modified_by']=request.user.id

        serializer = PostDetailsSerializer(post_obj,data=data,partial=True)

        if not serializer.is_valid():
            transaction.rollback()
            return Response({"status":"error","message":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        transaction.commit()
        return Response({"status":"success","message":"User details updated successfully"})

class CommentsView(APIView):
    def get(self,request):
        try:
            domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
            iu_master = get_iuobj(domain)
            post_id=request.query_params.get('post_id')
            parent_comment_id=request.query_params.get('parent_comment_id',None)
            if parent_comment_id is None:
                comments_detail=Comments.objects.filter(is_active=True,iu_id=iu_master,post_id=post_id,is_removed_comment=False,parent_comment__isnull=True)
            else:
                comments_detail=Comments.objects.filter(is_active=True,iu_id=iu_master,post_id=post_id,is_removed_comment=False,id=parent_comment_id)
            serializer=CommentsSerializer(comments_detail,many=True,fields=['id','message','list_tag_users','subcomments'])
            return Response({"status":"success","message":serializer.data},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_400_BAD_REQUEST)

    def post(self,request):
        try:
            data=request.data
            domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
            iu_master = get_iuobj(domain)
            if not iu_master :
                return Response({"status":"error","message":"UNAUTHORIZED DOMAIN"},status=status.HTTP_404_NOT_FOUND)
            data['user']=request.user.id
            data['created_by']=request.user.id
            data['iu_id']=iu_master.id
            current_time=int(timezone.now().timestamp())
            data['timestamp']=current_time
            parent_comm=request.data.get("parent_comment")
            if parent_comm:
                data['sub_comment']=True
            serializer=CommentsSerializer(data=data)
            if not serializer.is_valid():
                return Response({"status":"errors","message":serializer.errors},status=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            return Response({"status":"success","message":"comment added successfully"},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self,request):
        try:
            id=request.data.get('comment_id')
            domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
            iu_master = get_iuobj(domain)
            if not iu_master :
                    return Response({"status":"error","message":"UNAUTHORIZED DOMAIN"},status=status.HTTP_404_NOT_FOUND)
            user_role=get_user_roles(request)
            if user_role in "publisher":
                user_comment=Comments.objects.get(id=id,is_active=True,iu_id=iu_master)
                if not user_comment.post.publisher == request.user:
                    return Response({"status":"error","message":"unauthorized publisher for the post"},status=status.HTTP_400_BAD_REQUEST)
            else:
                user_comment=Comments.objects.get(id=id,user=request.user,is_active=True,iu_id=iu_master)
            user_comment.is_removed_comment=True
            user_comment.is_active=False
            user_comment.save()
            return Response({"status":"success","message":"comment deleted successfully"},status=status.HTTP_200_OK)
        except Comments.DoesNotExist:
            return Response({"status":"error","message":"Comments does not exist"},status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_400_BAD_REQUEST)

class LikeAPI(APIView):
    def get(self,request):
        try:
            post_id=request.query_params.get('post_id',None)
            domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
            iu_master = get_iuobj(domain)
            post=PostDetails.objects.get(pk=post_id,is_active=True,iu_id=iu_master,is_archived=False,post_status='published')
            req_det=GetCustomUserSerializer(post.likes_users_list.all(),many=True)
            return Response({"status":"success","message":req_det.data},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_400_BAD_REQUEST)
    
    def put(self,request):
        try:
            user=request.user
            post_id=request.data.get('post_id')
            domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
            iu_master = get_iuobj(domain)
            Post_detail=PostDetails.objects.get(id=post_id,is_active=True,iu_id=iu_master,post_status='published',is_archived=False)
            user_like=Post_detail.likes_users_list.filter(id=user.id).count()
            print(user_like)
            if user_like>0:
                Post_detail.likes_users_list.remove(user)
                return Response({"status":"success","message":"like removed successfully"},status=status.HTTP_200_OK)
            Post_detail.likes_users_list.add(user)
            return Response({"status":"success","message":"like addeds successfully"},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_400_BAD_REQUEST)
        
class ShareAPi(APIView):
    def get(self,request):
        try:
            post_id=request.query_params.get('post_id',None)
            if post_id is None:
              return Response({"status":"error","message":"post_id is required"},status=status.HTTP_400_BAD_REQUEST)
            domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
            iu_master = get_iuobj(domain)
            post=PostDetails.objects.get(pk=post_id,is_active=True,iu_id=iu_master,is_archived=False,post_status='published')
            req_det=GetCustomUserSerializer(post.shared_users_list.all(),many=True)
            return Response({"status":"success","message":req_det.data},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_400_BAD_REQUEST)
    
    def post(self,request):
        try:
            user=request.user
            post_id=request.data.get('post_id')
            domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
            iu_master = get_iuobj(domain)
            Post_detail=PostDetails.objects.get(id=post_id,is_active=True,iu_id=iu_master,post_status='published',is_archived=False)
            Post_detail.shared_users_list.add(user)
            return Response({"status":"success","message":"post shared successfully"},status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_400_BAD_REQUEST)


