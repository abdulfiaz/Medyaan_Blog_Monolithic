from django.shortcuts import render
from notification.serializers import TemplateMasterSerializer,EventMasterSerializer,GetEventMasterSerializer,GetTemplateMasterSerializer
from rest_framework.views import APIView,status
from rest_framework.response import Response
from users.auth import get_user_roles
from django.conf import settings
from adminapp.iudetail import get_iuobj    
from django.db import transaction
from notification.models import *

class TemplateMasterView(APIView):
    def get(self,request):
        template_id = request.query_params.get('template_id')
        user_role = get_user_roles(request)
        if user_role != 'admin':
            return Response({"status":"error","message":"You are unauthorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)
        
        if template_id:
            template = TemplateMaster.objects.get(id=template_id,is_active=True)
            serializer = GetTemplateMasterSerializer(template)

        else:
            templates = TemplateMaster.objects.filter(is_active=True)
            serializer = GetTemplateMasterSerializer(templates, many=True)
        
        return Response({'status': 'success', 'message': 'successfully receive data.','data':serializer.data},status=status.HTTP_200_OK)

    def post(self,request):
        template_name = request.data.get('template_name')
        user_role = get_user_roles(request)
        if user_role != 'admin':
            return Response({"status":"error","message":"You are unauthorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            template_obj = TemplateMaster.objects.get(template_name=template_name,is_active=True)
            return Response({"status":"error","message":"Template already exists!"},status=status.HTTP_400_BAD_REQUEST)
        except TemplateMaster.DoesNotExist:
            pass

        transaction.set_autocommit(False)
        data=request.data
        data['created_by']=request.user.id

        serializer = TemplateMasterSerializer(data=data)

        if not serializer.is_valid():
            transaction.rollback()
            return Response({"status":'error',"message":serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        transaction.commit()

        return Response({"status":"success","message":"TemplateMaster created successfully"},status=status.HTTP_201_CREATED)
    
    def put(self,request):
        template_id = request.data.get('template_id')
        user_role = get_user_roles(request)
        if user_role != 'admin':
            return Response({"status":"error","message":"You are unauthorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            template_obj = TemplateMaster.objects.get(id=template_id,is_active=True)
        except TemplateMaster.DoesNotExist:
            return Response({"error": "Template not found."}, status=status.HTTP_404_NOT_FOUND)
        
        transaction.set_autocommit(False)
        data=request.data
        data['modified_by']=request.user.id
        serializer = TemplateMasterSerializer(template_obj,data=data,partial=True)

        if not serializer.is_valid():
            transaction.rollback()
            return Response({"status":'error',"message":serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        transaction.commit()

        return Response({"status":"success","message":"TemplateMaster updated successfully"},status=status.HTTP_201_CREATED)
    
    def delete(self,request):
        template_id = request.data.get('template_id')
        user_role = get_user_roles(request)
        if user_role != 'admin':
            return Response({"status":"error","message":"You are unauthorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            template_obj = TemplateMaster.objects.get(id=template_id,is_active=True)
        except TemplateMaster.DoesNotExist:
            return Response({"error": "Template not found."}, status=status.HTTP_404_NOT_FOUND)
        
        template_obj.is_active=False
        template_obj.modified_by=request.user.id
        template_obj.save()

        return Response({"status":"success","message":"TemplateMaster deleted successfully"},status=status.HTTP_201_CREATED)
    
class EventMasterView(APIView):
    def get(self,request):
        event_id = request.query_params.get('event_id')
        
        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
        iu_obj = get_iuobj(domain)
        
        if not iu_obj :
            return Response({"status":"error","message":"Unauthorized domain"},status=status.HTTP_401_UNAUTHORIZED)      
        
        user_role = get_user_roles(request)
        
        if user_role != 'admin':
            return Response({"status":"error","message":"You are unauthorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)
        
        if event_id:
            template = EventMaster.objects.get(id=event_id,is_active=True,iu_id=iu_obj)
            serializer = GetEventMasterSerializer(template)

        else:
            templates = EventMaster.objects.filter(is_active=True)
            serializer = GetEventMasterSerializer(templates, many=True)
        
        return Response({'status': 'success', 'message': 'successfully receive data.','data':serializer.data},status=status.HTTP_200_OK)

    def post(self,request):
        name = request.data.get('name')
        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
        iu_obj = get_iuobj(domain)
        if not iu_obj :
            return Response({"status":"error","message":"Unauthorized domain"},status=status.HTTP_401_UNAUTHORIZED)        

        user_role = get_user_roles(request)

        if user_role != 'admin':
            return Response({"status":"error","message":"You are unauthorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)
        
        print("name",name)
        try:
            eventmaster_obj=EventMaster.objects.get(name=name,is_active=True,iu_id=iu_obj)
            return Response({"status":"error","message":"Eventmaster already exists"},status=status.HTTP_400_BAD_REQUEST)
        except EventMaster.DoesNotExist:
            pass
        
        try:
            template_obj = TemplateMaster.objects.get(template_name=name,is_active=True)
        except TemplateMaster.DoesNotExist:
            return Response({"status":"error",'message':"template doesnt found!"})
        
        
        transaction.set_autocommit(False)
        data = request.data
        data['template_id']=template_obj.id
        data['iu_id']=iu_obj.id
        data['created_by']=request.user.id

        serializer = EventMasterSerializer(data=data)

        if not serializer.is_valid():
            transaction.rollback()
            return Response({"status":"error","message":serializer.errors},status=status.HTTP_404_NOT_FOUND)
        
        serializer.save()
        transaction.commit()
        return Response({"status":"success","message":"EventMaster created successfully"},status=status.HTTP_201_CREATED)
    
    def put(self,request):
        event_id = request.data.get('event_id')
        
        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
        iu_obj = get_iuobj(domain)
        
        if not iu_obj :
            return Response({"status":"error","message":"Unauthorized domain"},status=status.HTTP_401_UNAUTHORIZED)        

        user_role = get_user_roles(request)

        if user_role != 'admin':
            return Response({"status":"error","message":"You are unauthorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            eventmaster_obj = EventMaster.objects.get(id=event_id,is_active=True,iu_id=iu_obj)
        except EventMaster.DoesNotExist:
            return Response({"status":"error","message":"Eventmaster doesnt found!"},status=status.HTTP_404_NOT_FOUND)
        
        transaction.set_autocommit(False)
        data=request.data
        data['modified_by']=request.user.id

        serializer = EventMasterSerializer(eventmaster_obj,data=data,partial=True)

        if not serializer.is_valid():
            transaction.rollback()
            return Response({"status":'error',"message":serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        transaction.commit()

        return Response({"status":"success","message":"EventMaster updated successfully"},status=status.HTTP_201_CREATED)
    
    def delete(self,request):
        event_id = request.data.get('event_id')
        
        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
        iu_obj = get_iuobj(domain)
        
        if not iu_obj :
            return Response({"status":"error","message":"Unauthorized domain"},status=status.HTTP_401_UNAUTHORIZED)        
        user_role = get_user_roles(request)
        
        if user_role != 'admin':
            return Response({"status":"error","message":"You are unauthorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            eventmaster_obj = EventMaster.objects.get(id=event_id,is_active=True,iu_id=iu_obj)
        except EventMaster.DoesNotExist:
            return Response({"error": "eventmaster not found."}, status=status.HTTP_404_NOT_FOUND)
        
        eventmaster_obj.is_active=False
        eventmaster_obj.modified_by=request.user.id
        eventmaster_obj.save()

        return Response({"status":"success","message":"EventMaster deleted successfully"},status=status.HTTP_201_CREATED)






        

        



