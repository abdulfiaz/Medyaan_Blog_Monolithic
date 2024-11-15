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
    event_organizer = serializers.SerializerMethodField()
    event_name = serializers.CharField(source='event.name')
    event_amount = serializers.DecimalField(source='event.event_amount', max_digits=10, decimal_places=2)
    event_longitude = serializers.CharField(source='event.longitude', default=None)
    event_latitude = serializers.CharField(source='event.latitude', default=None)
    event_address = serializers.CharField(source='event.address', default=None)

    class Meta:
        model = EventBookingDetails
        fields = ['id', 'no_of_tickets', 'booking_status', 'payment_status','event_detail_status', 'total_ticket_price', 'booking_date','event_name','event_amount','event_longitude','event_latitude','event_address','user_profile','event_organizer']

    
    def get_user_profile(self, obj):
        profile = obj.user.userdetails.first()
        if profile:
            return {'id': profile.id,'firstname': profile.firstname,'lastname': profile.lastname,'mobile_number': profile.user.mobile_number,'email': profile.user.email,'address':profile.primary_address }
        return None

    def get_event_detail_status(self, obj):
        if obj.event.event_date > timezone.now():
            return "upcoming"
        else:
            return "completed"
    
    def get_total_ticket_price(self, obj):
        return obj.total

    def get_event_organizer(self, obj):
        organizer = obj.event.event_organizer
        organizer_profile = organizer.userdetails.first() 

        if organizer_profile:
            return {
                'id': organizer.id,
                'firstname': organizer_profile.firstname,
                'lastname': organizer_profile.lastname,
                'email': organizer.email,
                'primary_address': organizer_profile.primary_address,
                'secondary_address': organizer_profile.secondary_address
            }
        return None





