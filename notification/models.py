from django.db import models
from adminapp .models import BaseModel,IUMaster
from users.models import CustomUser


class TemplateMaster(BaseModel):
    template_name = models.CharField(max_length=100,blank=True,null=True)
    content = models.TextField(blank=True,null=True)
    iu_id = models.ForeignKey(IUMaster, related_name='templatemaster_iu_id', on_delete=models.DO_NOTHING)

    class Meta:
        db_table = 'template_master'
        ordering = ['created_at']

class EventMaster(BaseModel):
    name = models.CharField(max_length=100, null=True, blank=True)
    email = models.BooleanField(default=False)
    sms = models.BooleanField(default=False)
    web = models.BooleanField(default=False)
    role = models.CharField(max_length=50, null=True, blank=True)
    template_id = models.ForeignKey(TemplateMaster,related_name='eventmaster_template', on_delete=models.DO_NOTHING)
    iu_id = models.ForeignKey(IUMaster, related_name='eventmaster_iu_id', on_delete=models.DO_NOTHING)

    class Meta:
        db_table = 'event_master'
        ordering = ['created_at']

class Notification(BaseModel):
    event = models.ForeignKey(EventMaster,related_name='event_id', on_delete=models.DO_NOTHING)
    sender = models.ForeignKey(CustomUser, blank=True, null=True,related_name='notification_sender', on_delete=models.DO_NOTHING)
    receiver = models.ForeignKey(CustomUser, blank=True, null=True,related_name='notification_receiver', on_delete=models.DO_NOTHING)
    subject = models.CharField(max_length=100,blank=True, null=True)
    message=models.TextField(blank=True,null=True)
    email_id = models.CharField(max_length=100,null=True,blank=True)
    email_message = models.TextField(blank=True, null=True)
    sms_message = models.TextField(blank=True, null=True)
    web_message = models.TextField(blank=True, null=True)
    redirect_link = models.CharField(max_length=100,blank=True, null=True) 
    role = models.CharField(max_length=100, null=True, blank=True)
    iu_id = models.ForeignKey(IUMaster, related_name='notification_iu_id', on_delete=models.DO_NOTHING)

    class Meta:
        db_table = 'notification'
        ordering = ['created_at']
