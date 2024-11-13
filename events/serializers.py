from rest_framework import serializers
from events.models import EventDetails,EventBookingDetails
from django.utils import timezone

class EventDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventDetails
        fields = '__all__'

class GetEventDetailsSerializer(serializers.ModelSerializer):
    user_profile = serializers.SerializerMethodField()
    class Meta:
        model = EventDetails
        fields = ['id','event_organizer','name','description','event_date','event_amount','event_member_limit','refund_applicable','payment_needed','longitude','latitude','address','user_profile']

    def get_user_profile(self, obj):
        profile = obj.event_organizer.userdetails.first()

        if profile:
            return {'id': profile.id,'firstname': profile.firstname,'lastname': profile.lastname,'mobile_number':profile.user.mobile_number,'email':profile.user.email}
        return None

class EventBookingDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventBookingDetails
        fields = '__all__'

class GetEventBookingDetailsSerializer(serializers.ModelSerializer):
    user_profile = serializers.SerializerMethodField()
    event_detail_status = serializers.SerializerMethodField()
    total_ticket_price = serializers.SerializerMethodField()

    class Meta:
        model = EventBookingDetails
        fields = ['id', 'no_of_tickets', 'booking_status', 'payment_status','event_detail_status', 'total_ticket_price', 'booking_date', 'user_profile']
    
    def get_user_profile(self, obj):
        profile = obj.user.userdetails.first()
        if profile:
            return {'id': profile.id,'firstname': profile.firstname,'lastname': profile.lastname,'mobile_number': profile.user.mobile_number,'email': profile.user.email }
        return None

    def get_event_detail_status(self, obj):
        if obj.event.event_date > timezone.now():
            return "upcoming"
        else:
            return "completed"
    
    def get_total_ticket_price(self, obj):
        return obj.total

