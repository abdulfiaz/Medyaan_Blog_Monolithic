from rest_framework import serializers
from notification.models import TemplateMaster,EventMaster,Notification

class TemplateMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateMaster
        fields = '__all__'

class GetTemplateMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = TemplateMaster
        fields = ['id','template_name','content']

class EventMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventMaster
        fields = '__all__'

class GetEventMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventMaster
        fields = ['id','template_id','name','email','sms','web','role']
    
