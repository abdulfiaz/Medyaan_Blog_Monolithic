from django.urls import path
from events.views import *
from django.conf.urls import url

app_name = 'events'

urlpatterns = [
    path('eventdetails/',EventDetailsView.as_view(),name='eventdetails'),

]