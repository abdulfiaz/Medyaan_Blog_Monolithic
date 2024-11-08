from django.shortcuts import render
from rest_framework.views import APIView,status
from rest_framework.response import Response
from posts.serializers import PostCategorySerializer,GetPostCategorySerializer,PostDetailsSerializer,GetPostDetailsSerializer
from posts.models import PostCategory,PostDetails
from users.models import PublisherProfile
from users.auth import get_user_roles
from django.conf import settings
from adminapp.iudetail import get_iuobj    
from django.db import transaction


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
        pass

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
        counts={}
        if approved_status == 'pending':
            users = PostDetails.objects.filter(post_status='pending',iu_id=iu_master,is_active=True)
        elif approved_status == 'published':
            users = PostDetails.objects.filter(post_status='published',iu_id=iu_master,is_active=True)
        elif approved_status == 'rejected':
            users = PostDetails.objects.filter(post_status='rejected',iu_id=iu_master,is_active=True)
        
        all_data= PostDetails.objects.filter(iu_id=iu_master, is_active=True)
        counts['total_posts'] = all_data.count()
        counts['status_pending'] = all_data.filter(post_status='pending').count()
        counts['status_published'] = all_data.filter(post_status='published').count()
        counts['status_rejected'] = all_data.filter(post_status='rejected').count()
    

        user_data = GetPostDetailsSerializer(users, many=True)
        return Response({"status":"success","message":"data retrieved successfully","data": user_data.data,"counts": counts}, status=status.HTTP_200_OK)

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



