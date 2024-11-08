from django.urls import path
from posts.views import *
from django.conf.urls import url


app_name = 'posts'


urlpatterns = [
    path('category/',PostCategoryView.as_view(),name='post_category'),
    path('post_details/',PostDetailsView.as_view(),name='posts'),
    path('post_approval/',PostApprovalView.as_view(),name='post_approval')

]