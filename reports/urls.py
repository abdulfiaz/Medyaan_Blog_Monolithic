from django.urls import path
from reports.views import *
from django.conf.urls import url

app_name = 'reports'

urlpatterns = [
    path('eventreports/',EventReport.as_view())

]