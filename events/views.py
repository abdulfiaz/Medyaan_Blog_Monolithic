from django.shortcuts import render
from rest_framework.views import APIView,status
from rest_framework.response import Response
from events.serializers import EventDetailsSerializer
from events.models import EventDetails
from users.models import PublisherProfile
from users.auth import get_user_roles
from django.conf import settings
from adminapp.iudetail import get_iuobj    
from django.db import transaction

class EventDetailsView(APIView):
    def get(self,requset):
        pass

    def post(self,request):
        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
        iu_master = get_iuobj(domain)
        if not iu_master :
            return Response({"status":"error","message":"Unauthorized domain"},status=status.HTTP_401_UNAUTHORIZED)        

        user_role = get_user_roles(request)

        if user_role != 'eventorganiser':
            return Response({"status":"error","message":"You are unauthorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)
        
        eventorganizer_status = PublisherProfile.objects.get(user=request.user,is_active=True,role_type='eventorganiser',is_rejected=False,iu_id=iu_master)
        if eventorganizer_status.approved_status != 'approved':
            return Response({"status":"error","message":"Your approval is still pending!"},status=status.HTTP_401_UNAUTHORIZED)
        
        transaction.set_autocommit(False)
        data = request.data
        data['event_organizer'] = request.user.id
        data['created_by'] = request.user.id
        data['iu_id']=iu_master.id

        serializer = EventDetailsSerializer(data=data)

        if not serializer.is_valid():
            transaction.rollback()
            return Response({"status":"error","message":serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        
        event = serializer.save()
        transaction.commit()
        return Response({"status":"success","message":"Event created successfully","data":{'id':event.id,'event_date':event.event_date}},status=status.HTTP_201_CREATED)
    
    def put(self,request):
        event_id = request.data.get('event_id')

        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
        iu_master = get_iuobj(domain)
        if not iu_master :
            return Response({"status":"error","message":"Unauthorized domain"},status=status.HTTP_401_UNAUTHORIZED)
        
        if not event_id:
            return Response({"status":"error","message":"event_id is required"},status=status.HTTP_400_BAD_REQUEST)
        
        try:
            event_obj = EventDetails.objects.get(id=event_id,event_organizer=request.user,event_status='approved',is_active=True,iu_id=iu_master)
        except EventDetails.DoesNotExist:
            return Response({"status":"error","message":"Event not found"},status=status.HTTP_404_NOT_FOUND)
        
        data =request.data
        data['modified_by']=request.user.id
        data['event_status']='pending'

        serializer = EventDetailsSerializer(event_obj,data=data,partial=True)

        if not serializer.is_valid():
            transaction.rollback()
            return Response({"status":"error","message":serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        transaction.commit()
        return Response({"status":"success","message":"event updated successfully!"},status=status.HTTP_201_CREATED)