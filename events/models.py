from django.db import models
from adminapp.models import BaseModel,IUMaster
from users.models import CustomUser
from django.contrib.postgres.fields import JSONField,ArrayField
from django.utils import timezone

class EventDetails(BaseModel):
    name = models.CharField(max_length=50)
    description = models.CharField(max_length = 300,null=True,blank=True)
    event_organizer = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='event_organizer_id')
    event_date = models.DateTimeField(null=True)
    payment_needed = models.BooleanField(default=False)
    event_amount = models.DecimalField(max_digits=10, decimal_places=3,default=0)
    event_member_limit = models.IntegerField()
    instructions=models.TextField(blank=True,null=True)
    inclusions=models.TextField(blank=True,null=True)
    is_refund_applicable = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    longitude = models.CharField(max_length=20, null=True, blank=True)
    latitude = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField()
    event_status = models.CharField(default='pending',max_length=50)
    rejected_reason = models.CharField(max_length=50,blank=True,null=True)
    
    iu_id=models.ForeignKey(IUMaster,related_name='eventdetails_iu',on_delete = models.CASCADE)

    class Meta:
        db_table='event_details'
        ordering = ['created_at'] 

class EventBookingDetails(BaseModel):
    event = models.ForeignKey(EventDetails,on_delete=models.CASCADE,related_name='event_id')
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='event_booking_user')
    event_details = JSONField(default=dict, blank=True)
    booking_date = models.DateTimeField(auto_now_add=True)
    no_of_tickets = models.IntegerField(default=0)
    payment_status = models.BooleanField(default=False) #false means unpaid and true meand paid
    booking_status = models.CharField(default='confirmed',max_length=20)
    cancellation_reason = models.CharField(max_length=100,null=True,blank=True)
    cancelled_by = models.CharField(max_length=15,blank=True,null=True)
    cancelled_at = models.DateTimeField(null=True)
    refund_status = models.CharField(default='pending',max_length=20)
    is_archived = models.BooleanField(default=False)
    vat = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    iu_id=models.ForeignKey(IUMaster,related_name='eventbookingdetails_iu',on_delete = models.CASCADE)


    class Meta:
        db_table='event_booking_details'
        ordering = ['created_at'] 

class EventBookmarkDetails(BaseModel):
    user = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='bookmark_user')
    event = models.ForeignKey(EventDetails,on_delete=models.CASCADE,related_name='bookmark_event')
    is_removed = models.BooleanField(default=False)
    iu_id = models.ForeignKey(IUMaster, on_delete=models.CASCADE, related_name='bookmark_iu')

    class Meta:
        db_table = 'event_bookmark_details'
        ordering = ['created_at']
