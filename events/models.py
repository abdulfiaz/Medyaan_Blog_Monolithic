from django.db import models
from adminapp.models import BaseModel,IUMaster
from users.models import CustomUser

class EventDetails(BaseModel):
    event_organizer = models.ForeignKey(CustomUser,on_delete=models.CASCADE,related_name='event_organizer_id')
    event_date = models.DateTimeField()
    event_amount = models.DecimalField(max_digits=10, decimal_places=2,default=0)
    event_member_limit = models.IntegerField()
    refund_applicable = models.BooleanField(default=False)
    payment_needed = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    longitude = models.CharField(max_length=20, null=True, blank=True)
    latitude = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField()
    iu_id=models.ForeignKey(IUMaster,related_name='eventdetails_iu',on_delete = models.CASCADE)

    class Meta:
        db_table='event_details'
        ordering = ['created_at'] 


