from rest_framework import serializers
from adminapp.models import IUMaster


class IUMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = IUMaster
        fields = "__all__"