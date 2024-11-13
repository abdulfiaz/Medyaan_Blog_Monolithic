from django.shortcuts import render
from datetime import datetime
from django.utils import timezone
from rest_framework.views import APIView,status
from rest_framework.response import Response
from events.serializers import EventDetailsSerializer,GetEventDetailsSerializer,EventBookingDetailsSerializer,GetEventBookingDetailsSerializer
from events.models import EventDetails,EventBookingDetails
from users.models import PublisherProfile
from users.auth import get_user_roles
from django.conf import settings
from adminapp.iudetail import get_iuobj    
from django.db import transaction

class EventDetailsView(APIView):
    def get(self,request):
        event_date = request.query_params.get('date')
        event_organizer = request.query_params.get('event_organizer')

        if event_date:
            try:
                date_obj = datetime.strptime(event_date, '%Y-%m-%d').date()
            except ValueError:
                return Response({"status": "error", "message": "Invalid date format. Use YYYY-MM-DD."},status=status.HTTP_400_BAD_REQUEST)

            events = EventDetails.objects.filter(event_date__date=date_obj,is_active=True).order_by('-created_at')
        elif event_organizer:
            events = EventDetails.objects.filter(event_organizer=event_organizer,is_active=True).order_by('-created_at')
        else:
            events = EventDetails.objects.filter(event_date__gt=timezone.now(),is_active=True).order_by('-created_at')

        event_list = []
        for event in events:
            event_data = GetEventDetailsSerializer(event).data
            event_data['event_detailed_status'] = 'upcoming' if event.event_date > timezone.now() else 'completed'
            event_list.append(event_data)

        return Response({"status": "success", "message": "Events retrieved successfully", "data": event_list},status=status.HTTP_200_OK)

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
            event_obj = EventDetails.objects.get(id=event_id,event_organizer=request.user,event_status='published',is_active=True,iu_id=iu_master)
        except EventDetails.DoesNotExist:
            return Response({"status":"error","message":"Event not found"},status=status.HTTP_404_NOT_FOUND)
        
        transaction.set_autocommit(False)
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
    
    def delete(self,request):
        try:
            event_id = request.data.get('event_id')
            domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
            iu_master = get_iuobj(domain)
            if not iu_master :
                return Response({"status":"error","message":"Unauthorized domain"},status=status.HTTP_401_UNAUTHORIZED)        

            user_role = get_user_roles(request)
            try:
                if user_role == 'manager':
                    event_obj = EventDetails.objects.get(id=event_id,event_status='published',is_active=True,iu_id=iu_master)
                elif user_role == 'eventorganiser':
                    event_obj = EventDetails.objects.get(id=event_id,event_status='published',is_active=True,event_organizer=request.user.id,iu_id=iu_master)
            except EventDetails.DoesNotExist:
                return Response({"status":"error","message":"event not found"},status=status.HTTP_404_NOT_FOUND)
            
            event_obj.is_active=False
            event_obj.is_archived=True
            event_obj.modified_by=request.user.id
            event_obj.save()

            return Response({"status":"success","message":"event deleted successfully !"},status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_403_FORBIDDEN)
        
class EventApproval(APIView):
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
        
        all_data = EventDetails.objects.filter(iu_id=iu_master, is_active=True)
        events = all_data.filter(event_status=approved_status)

        counts['total_posts'] = all_data.count()
        approved_statuses = ['pending', 'published', 'rejected']
        for event_status in approved_statuses:
            counts[f'status_{event_status}'] = all_data.filter(event_status=event_status).count()

        event_data = GetEventDetailsSerializer(events, many=True)
        return Response({"status":"success","message":"data retrieved successfully","data": event_data.data,"counts": counts},status=status.HTTP_200_OK)

    def put(self,request):
        event_id=request.data.get("event_id")
        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
        iu_master = get_iuobj(domain)
        if not iu_master :
            return Response({"status":"error","message":"Unauthorized domain"},status=status.HTTP_401_UNAUTHORIZED)        

        user_role = get_user_roles(request)

        if user_role!= 'manager':
            return Response({"status":"error","message":"You are unauthorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            event_obj = EventDetails.objects.get(id=event_id,event_status='pending',is_active=True,iu_id=iu_master)
        except EventDetails.DoesNotExist:
            return Response({"status":"error","message":"Event not found"},status=status.HTTP_404_NOT_FOUND)
        
        transaction.set_autocommit(False)
        data=request.data
        data['modified_by']=request.user.id
        data['iu_id']=iu_master.id

        serializer = EventDetailsSerializer(event_obj,data=data,partial=True)

        if not serializer.is_valid():
            transaction.rollback()
            return Response({"status":"error","message":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        transaction.commit()
        return Response({"status":"success","message":"Event details updated successfully"})

class EventBookingDetailsView(APIView):
    def get(self, request):
        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
        event_id = request.query_params.get('event_id',None)
        iu_master = get_iuobj(domain)
        
        if not iu_master:
            return Response({"status": "error", "message": "Unauthorized domain"}, status=status.HTTP_401_UNAUTHORIZED)
        
        user_roles = get_user_roles(request)

        if user_roles == 'eventorganiser':
            if not event_id:
                return Response({"status": "error", "message": "event_id is required for event organizers"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                event_obj = EventDetails.objects.get(id=event_id, is_active=True, iu_id=iu_master)
                bookings = EventBookingDetails.objects.filter(event=event_obj, is_active=True)
            except EventDetails.DoesNotExist:
                return Response({"status": "error", "message": "Event not found"}, status=status.HTTP_404_NOT_FOUND)
        
        elif user_roles == 'consumer':
            bookings = EventBookingDetails.objects.filter(user=request.user, is_active=True)
        
        else:
            return Response({"status": "error", "message": "Unauthorized role"}, status=status.HTTP_403_FORBIDDEN)

        serializer = GetEventBookingDetailsSerializer(bookings, many=True)
        return Response({"status": "success", "data": serializer.data}, status=status.HTTP_200_OK)

    def post(self,request):
        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
        event_id = request.data.get('event')
        no_of_tickets = request.data.get('no_of_tickets',1)
        iu_master = get_iuobj(domain)
        if not iu_master :
            return Response({"status":"error","message":"Unauthorized domain"},status=status.HTTP_401_UNAUTHORIZED)  
        
        if not event_id:
            return Response({"status":"error","message":"event id is required"},status=status.HTTP_400_BAD_REQUEST)
        
        try:
            event_obj = EventDetails.objects.get(id=event_id,iu_id=iu_master,is_active=True)
        except EventDetails.DoesNotExist:
            return Response({"status":"error","message":"event details not found!"},status=status.HTTP_404_NOT_FOUND)
        
        payment_status_obj = 'paid' if event_obj.payment_needed else 'unpaid'

        sub_total = no_of_tickets * event_obj.event_amount
        vat = (0+event_obj.event_amount)/100
        total = vat + sub_total

        transaction.set_autocommit(False)
        data=request.data
        data['iu_id']=iu_master.id
        data['user']=request.user.id
        data['created_by']=request.user.id
        data['payment_status']=payment_status_obj
        data['sub_total']=sub_total
        data['total']=total

        serializer = EventBookingDetailsSerializer(data=data)

        if not serializer.is_valid():
            transaction.rollback()
            return Response({"status":"error","message":serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        
        event_booking = serializer.save()
        transaction.commit()
        return Response({"status":"success","message":"Event booking created successfully","data":{'id':event_booking.id,'booking_date':event_booking.booking_date}},status=status.HTTP_201_CREATED)


            
        

        


