from django.shortcuts import render
from datetime import datetime,timedelta
from django.utils.dateformat import format as date_format
from django.utils import timezone
from rest_framework.views import APIView,status
from rest_framework.response import Response
from events.serializers import *
from events.models import *
from posts.serializers import *
from users.models import PublisherProfile
from users.auth import get_user_roles
from django.conf import settings
from adminapp.iudetail import get_iuobj    
from django.db import transaction
from django.template.loader import render_to_string
from notification.models import TemplateMaster,EventMaster
from adminapp.utils import get_notification
from sdd_blog import settings


class EventDetailsView(APIView): 
    def get(self,request):
        user_role = get_user_roles(request)
        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
        iu_obj = get_iuobj(domain)
        if not iu_obj :
            return Response({"status":"error","message":"Unauthorized domain"},status=status.HTTP_401_UNAUTHORIZED)

        if user_role == 'eventorganiser':
            events = EventDetails.objects.filter(event_organizer=request.user.id,iu_id=iu_obj,is_active=True,event_status='published').order_by('-created_at')
            serializer=GetEventDetailsSerializer(events,many=True)
            cur_date=datetime.now()
            
            completed = events.filter(event_date__lt=cur_date).count()
            upcoming = events.filter(event_date__gte=cur_date).count()
            return Response({"status":"success","Total events count":events.count(),"completed_events":completed,"upcoming_events":upcoming,"data":serializer.data},status=status.HTTP_200_OK)
        
        

        elif user_role == 'consumer':
            event_date = request.query_params.get('date')
            event_organizer = request.query_params.get('event_organizer')
            address=request.query_params.get('search_address')

            if event_date:
                try:
                    date_obj = datetime.strptime(event_date, '%Y-%m-%d').date()
                except ValueError:
                    return Response({"status": "error", "message": "Invalid date format. Use YYYY-MM-DD."},status=status.HTTP_400_BAD_REQUEST)

                events = EventDetails.objects.filter(event_date__date=date_obj,is_active=True,iu_id=iu_obj,event_status='published').order_by('-created_at')
            elif event_organizer:
                events = EventDetails.objects.filter(event_organizer=event_organizer,is_active=True,iu_id=iu_obj).order_by('-created_at')
            
            elif address:
                events = EventDetails.objects.filter(address__icontains=address,is_active=True,iu_id=iu_obj).order_by('-created_at')

            else:
                events = EventDetails.objects.filter(event_date__gt=timezone.now(),is_active=True,iu_id=iu_obj).order_by('-created_at')

            event_list = []
            for event in events:
                event_data = GetEventDetailsSerializer(event).data
                event_data['event_detailed_status'] = 'upcoming' if event.event_date > timezone.now() else 'completed'
                event_list.append(event_data)

            return Response({"status": "success", "message": "Events retrieved successfully", "data": event_list},status=status.HTTP_200_OK)

    def post(self,request):
        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
        iu_obj = get_iuobj(domain)
        if not iu_obj :
            return Response({"status":"error","message":"Unauthorized domain"},status=status.HTTP_401_UNAUTHORIZED)        

        user_role = get_user_roles(request)

        if user_role != 'eventorganiser':
            return Response({"status":"error","message":"You are unauthorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)
        
        eventorganizer_status = PublisherProfile.objects.get(user=request.user,is_active=True,role_type='eventorganiser',is_rejected=False,iu_id=iu_obj)
        if eventorganizer_status.approved_status != 'approved':
            return Response({"status":"error","message":"Your approval is still pending!"},status=status.HTTP_401_UNAUTHORIZED)
        
        transaction.set_autocommit(False)
        data = request.data
        data['event_organizer'] = request.user.id
        data['created_by'] = request.user.id
        data['iu_id']=iu_obj.id

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
        iu_obj = get_iuobj(domain)
        if not iu_obj :
            return Response({"status":"error","message":"Unauthorized domain"},status=status.HTTP_401_UNAUTHORIZED)
        
        user_role = get_user_roles(request)
        if user_role != 'eventorganiser':
            return Response({"status":"error","message":"You are unauthorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)
        
        if not event_id:
            return Response({"status":"error","message":"event_id is required"},status=status.HTTP_400_BAD_REQUEST)
        
        try:
            event_obj = EventDetails.objects.get(id=event_id,event_organizer=request.user,event_status='published',is_active=True,iu_id=iu_obj)
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
            iu_obj = get_iuobj(domain)
            if not iu_obj :
                return Response({"status":"error","message":"Unauthorized domain"},status=status.HTTP_401_UNAUTHORIZED)        

            user_role = get_user_roles(request)

            event_booking_obj = EventBookingDetails.objects.filter(event=event_id, is_active=True, iu_id=iu_obj)
            if event_booking_obj:
                return Response({"status": "error", "message": "This event is unable to delete as it has bookings!"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                if user_role == 'manager':
                    event_obj = EventDetails.objects.get(id=event_id,event_status='published',is_active=True,iu_id=iu_obj)
                elif user_role == 'eventorganiser':
                    event_obj = EventDetails.objects.get(id=event_id,event_status='published',is_active=True,event_organizer=request.user.id,iu_id=iu_obj)
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
        iu_obj = get_iuobj(domain)
        if not iu_obj:
            return Response({'status': 'failure', 'message': 'Unauthorized domain'},status=status.HTTP_404_NOT_FOUND)

        if user_role != 'manager':
            return Response({"status":"error","message":"You are unaithorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)
        
        # to count the total of aproved_status'pending,approved,rejected' and total of all publisher,eventorganiser
        counts = {}
        
        all_data = EventDetails.objects.filter(iu_id=iu_obj, is_active=True)
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
        iu_obj = get_iuobj(domain)
        if not iu_obj :
            return Response({"status":"error","message":"Unauthorized domain"},status=status.HTTP_401_UNAUTHORIZED)        

        user_role = get_user_roles(request)

        if user_role!= 'manager':
            return Response({"status":"error","message":"You are unauthorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)
        
        try:
            event_obj = EventDetails.objects.get(id=event_id,event_status='pending',is_active=True,iu_id=iu_obj)
        except EventDetails.DoesNotExist:
            return Response({"status":"error","message":"Event not found"},status=status.HTTP_404_NOT_FOUND)
        
        transaction.set_autocommit(False)
        data=request.data
        data['modified_by']=request.user.id
        data['iu_id']=iu_obj.id

        serializer = EventDetailsSerializer(event_obj,data=data,partial=True)

        if not serializer.is_valid():
            transaction.rollback()
            return Response({"status":"error","message":serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()

         # template and email sending
        try:
            template=TemplateMaster.objects.get(template_name='event_approve/reject')
        except Exception as e:
            return Response({"status":"error","message":"template does not exist"},status=status.HTTP_400_BAD_REQUEST)
        
        event=EventMaster.objects.get(name=template.template_name,iu_id=iu_obj,is_active=True)
        event_approved_status=request.data.get('event_status')
        template_message=template.content.format(event_obj.name,event_approved_status)
        print(template_message)
        message="Your Event Approval"
    
        domain = request.get_host()  # Example: '127.0.0.1:8000'
        logo_url = f"http://{domain}/static/images/welcome.jpg"
        print(logo_url)
        

        content={
            "base64_image":logo_url,
            "message":message,
            "template_message":template_message
            
        }
        rendered_html_message = render_to_string('events/event_approval.html',content)
        sender_id=request.user.id
        receiver_id=event_obj.event_organizer.id
        subject="Status of your application"
        
        email_id=event_obj.event_organizer.email
        email_message=rendered_html_message
        role=event.role
        iu_id=iu_obj.id
        
        notification_data=get_notification(message,event,sender_id,receiver_id,subject,email_id,email_message,role,iu_id)
        if notification_data != 1:
            transaction.rollback()
            print(notification_data)


        # transaction.commit()
        return Response({"status":"success","message":"User details updated successfully"})
        transaction.commit()
        return Response({"status":"success","message":"Event details updated successfully"})

class EventBookingDetailsView(APIView):
    def get(self, request):
        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
        event_id = request.query_params.get('event_id',None)
        iu_obj = get_iuobj(domain)
        
        if not iu_obj:
            return Response({"status": "error", "message": "Unauthorized domain"}, status=status.HTTP_401_UNAUTHORIZED)
        
        user_roles = get_user_roles(request)

        if user_roles == 'eventorganiser':
            if not event_id:
                return Response({"status": "error", "message": "event_id is required for event organizers"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                event_obj = EventDetails.objects.get(id=event_id, is_active=True, iu_id=iu_obj,event_organizer=request.user)
                bookings = EventBookingDetails.objects.filter(event=event_obj, is_active=True,iu_id=iu_obj)
            except EventDetails.DoesNotExist:
                return Response({"status": "error", "message": "Event not found"}, status=status.HTTP_404_NOT_FOUND)  
        elif user_roles == 'consumer':
            bookings = EventBookingDetails.objects.filter(user=request.user, is_active=True,iu_id=iu_obj)
        
        else:
            return Response({"status": "error", "message": "Unauthorized role"}, status=status.HTTP_403_FORBIDDEN)

        completed_events=bookings.filter(booking_date__lt=timezone.now()).count()
        upcoming_events=bookings.filter(booking_date__gte=timezone.now()).count()
        serializer = GetEventBookingDetailsSerializer(bookings, many=True)
        return Response({"status": "success","completed_event":completed_events,"upcoming_events":upcoming_events, "data": serializer.data}, status=status.HTTP_200_OK)

    def post(self,request):
        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
        event_id = request.data.get('event')
        no_of_tickets = request.data.get('no_of_tickets',0)
        iu_obj = get_iuobj(domain)
        if not iu_obj :
            return Response({"status":"error","message":"Unauthorized domain"},status=status.HTTP_401_UNAUTHORIZED)  
        
        if not event_id:
            return Response({"status":"error","message":"event id is required"},status=status.HTTP_400_BAD_REQUEST)
        
        try:
            event_obj = EventDetails.objects.get(id=event_id,iu_id=iu_obj,is_active=True,event_status="published")
        except EventDetails.DoesNotExist:
            return Response({"status":"error","message":"event details not found!"},status=status.HTTP_404_NOT_FOUND)
        
        # payment_status_obj = True if event_obj.payment_needed else False

        sub_total = no_of_tickets * event_obj.event_amount
        vat = (settings.VAT+event_obj.event_amount)/100
        total = vat + sub_total

        transaction.set_autocommit(False)
        data=request.data
        data['iu_id']=iu_obj.id
        data['user']=request.user.id
        data['created_by']=request.user.id
        # data['payment_status']=payment_status_obj
        data['sub_total']=sub_total
        data['total']=total

        serializer = EventBookingDetailsSerializer(data=data)
        
        if not serializer.is_valid():
            transaction.rollback()
            return Response({"status":"error","message":serializer.errors},status=status.HTTP_400_BAD_REQUEST)
        
        event_obj.event_member_limit-=no_of_tickets
        event_obj.save()
        event_booking = serializer.save()
        transaction.commit()
        return Response({"status":"success","message":"Event booking created successfully","data":{'id':event_booking.id,'booking_date':event_booking.booking_date}},status=status.HTTP_201_CREATED)

    def put(self,request):
        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
        iu_obj = get_iuobj(domain)
        transaction.set_autocommit(False)
       
        if not iu_obj :
            return Response({"status":"error","message":"Unauthorized domain"},status=status.HTTP_401_UNAUTHORIZED)
       
        event_registration_id=request.data.get("event_registration_id")
       
        if not event_registration_id:
            transaction.rollback()
            return Response({"status":"error","message":"event id is required"},status=status.HTTP_400_BAD_REQUEST)
        
        try:
            event_registered_detail=EventBookingDetails.objects.get(id=event_registration_id,iu_id=iu_obj,is_active=True,is_archived=False,user=request.user)
       
        except EventBookingDetails.DoesNotExist:
            transaction.rollback()
            return Response({"status":"error","message":"regestration details does not exist"},status=status.HTTP_400_BAD_REQUEST)
        
        event_registered_detail.booking_status='cancelled'
       
        if event_registered_detail.payment_status =='paid':
            event_registered_detail.refund_status='refunded'
        event_registered_detail.modified_by=request.user.id
        event_registered_detail.save()
        
        try:
            event_detail=EventDetails.objects.get(id=event_registered_detail.event.id,is_active=True,iu_id=iu_obj,is_archived=False)
        except EventDetails.DoesNotExist:
            transaction.rollback()
            return Response({"status":"error","message":"event does not found"},status=status.HTTP_400_BAD_REQUEST)
        event_detail.event_member_limit+=event_registered_detail.no_of_tickets
        event_detail.save()
        transaction.commit()
        return Response({"status":"success","message":"tickets cancelled successfully"},status=status.HTTP_200_OK)

# bookmark for the events
class BookmarkView(APIView):
    def get(self,request):
        try:
            event_id = request.query_params.get('event_id')
            
            domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
            iu_obj = get_iuobj(domain)

            user_role = get_user_roles(request)
            if user_role != 'eventorganiser':
                return Response({"status":"error","message":"You are unauthorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)
        
            if not iu_obj:
                return Response({"status": "error", "message": "Unauthorized domain"}, status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                event_obj = EventDetails.objects.get(id=event_id,is_active=True,event_status='published',iu_id=iu_obj,event_organizer=request.user)
            except EventDetails.DoesNotExist:
                return Response({"status":"error","message":"Event Details doesnt exists!"},status=status.HTTP_404_NOT_FOUND)
            user_obj=GetCustomUserSerializer(event_obj.bookmark.all(),many=True)
            total_count=event_obj.bookmark.count()

            return Response({"status":"success","message":user_obj.data,"total_count":total_count})
        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_400_BAD_REQUEST)


    def put(self,request):
        try:
            event_id = request.data.get('event_id')
            domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
            iu_obj = get_iuobj(domain)
            user_role=get_user_roles(request)

            if not iu_obj :
                return Response({"status":"error","message":"Unauthorized domain"},status=status.HTTP_401_UNAUTHORIZED)
            
            if user_role != 'consumer':
                return Response({"status":"error","message":"You are unauthorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)
            
            event_obj = EventDetails.objects.get(id=event_id,is_active=True,iu_id=iu_obj,is_archived=False,event_status='published')
            bookmark_obj=event_obj.bookmark.filter(id=request.user.id).count()

            if bookmark_obj>0:
                event_obj.bookmark.remove(request.user)
                return Response({"status":"success","message":"Bookmark removed successfully!"},status=status.HTTP_200_OK)
            
            event_obj.bookmark.add(request.user)
            return Response({"status":"success","message":"Bookmark added successfully!"},status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_400_BAD_REQUEST)
            
            
