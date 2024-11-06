from django.shortcuts import render
from rest_framework.views import APIView,status
from rest_framework.response import Response
from posts.serializers import PostCategorySerializer,GetPostCategorySerializer
from posts.models import PostCategory
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
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
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
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
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

        


