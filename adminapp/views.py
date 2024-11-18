from django.shortcuts import render
from rest_framework.views import APIView,status
from rest_framework.response import Response
from django.db import transaction
from users.auth import get_user_roles
from adminapp.serializers import IUMasterSerializer
from adminapp.models import IUMaster

class IUMasterAPI(APIView):
    def get(self, request):
        id = request.query_params.get('id')
        rolename = get_user_roles(request)

        if rolename != 'admin':
            return Response({"status": "error", "message": "Only admin can have the access!"}, status=status.HTTP_403_FORBIDDEN)

        try:
            if id:
                try:
                    iumaster = IUMaster.objects.get(id=id, is_active=True)
                except IUMaster.DoesNotExist:
                    return Response({"status": "error", "message": "IUMaster not found"}, status=status.HTTP_404_NOT_FOUND)
                serializer = IUMasterSerializer(iumaster)
            else:
                iumaster = IUMaster.objects.filter(is_active=True)
                serializer = IUMasterSerializer(iumaster, many=True)
            
            return Response({"status": "success", "message": "IUMaster list retrieved successfully", "data": serializer.data}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    def post(self, request):
        rolename = get_user_roles(request)
        if rolename != "admin":
            return Response({"status": "error", "message": "Only admin can access this!"}, status=status.HTTP_403_FORBIDDEN)

        transaction.set_autocommit(False)
        data=request.data
        data['created_by']=request.user.id
        serializer = IUMasterSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            transaction.commit()
            return Response({"status": "success", "message": "Details created successfully"}, status=status.HTTP_201_CREATED)
        else :
            transaction.rollback()
            return Response({"status": "error", "message":  serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        id = request.data.get('id')
        rolename = get_user_roles(request)

        if rolename != "admin":
            return Response({"status": "error", "message": "Only admin can access this!"}, status=status.HTTP_403_FORBIDDEN)

        if not id:
            return Response({"status":"error","message":"id is required"})
        
        try:
            iumaster = IUMaster.objects.get(id=id, is_active=True)
        except IUMaster.DoesNotExist:
            return Response({"status": "error", "message": "IUMaster not found"}, status=status.HTTP_404_NOT_FOUND)
        
        transaction.set_autocommit(False)
        data=request.data
        data['modified_by']=request.user.id
        serializer = IUMasterSerializer(iumaster, data=data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            transaction.commit()
            return Response({"status": "success", "message": "Details updated successfully"}, status=status.HTTP_200_OK)
            
        else:
            transaction.rollback()
            return Response({"status": "error", "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        id = request.data.get('id')
        rolename = get_user_roles(request)

        if rolename != "admin":
            return Response({"status": "error", "message": "Only admin can access this!"}, status=status.HTTP_403_FORBIDDEN)
        if not id:
            return Response({"status":"error","message":"id is required"})
        
        try:
            iumaster = IUMaster.objects.get(id=id, is_active=True)
        except IUMaster.DoesNotExist:
            return Response({"status": "error", "message": "IUMaster not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            transaction.set_autocommit(False)
            iumaster.is_active = False
            iumaster.modified_by=request.user.id
            iumaster.save()
            transaction.commit()
            return Response({"status": "success", "message": "IU Master deleted successfully"}, status=status.HTTP_200_OK)

        except Exception as e:
            transaction.rollback()
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)