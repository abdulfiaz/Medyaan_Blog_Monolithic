from django.conf.urls import url
from django.urls import path
from notification.views import *

app_name = 'notification'

urlpatterns = [
    path('templatemaster/create/',TemplateMasterView.as_view()),
    path('eventmaster/create/',EventMasterView.as_view()),
]