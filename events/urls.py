from django.urls import path
from events.views import *
from django.conf.urls import url

app_name = 'events'

urlpatterns = [
    path('eventdetails/',EventDetailsView.as_view(),name='eventdetails'),
    path('approval/',EventApproval.as_view(),name='event_approval'),
    path('booking/',EventBookingDetailsView.as_view(),name='event_booking'),

]