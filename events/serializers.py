from rest_framework import serializers
from events.models import EventDetails

class EventDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventDetails
        fields = '__all__'