from rest_framework import serializers
from events.models import EventDetails

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