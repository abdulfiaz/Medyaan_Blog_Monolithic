from rest_framework import serializers
from events.models import EventDetails

class EventDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventDetails
        fields = '__all__'

class GetEventDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventDetails
        fields = ['id','name','description','event_date','event_amount','event_member_limit','refund_applicable','payment_needed','longitude','latitude','address']