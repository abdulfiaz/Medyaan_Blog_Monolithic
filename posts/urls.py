from django.urls import path
from posts.views import *
from django.conf.urls import url


app_name = 'posts'


urlpatterns = [
    path('category/',PostCategoryView.as_view(),name='post_category'),

]