from django.conf.urls import url
from django.urls import path
from users.views import *
from users.views import RoleMasterCreateView,CreateCustomUserView,ManagerApprovalView

app_name = 'users'

urlpatterns = [
    path('login/', login, name='login'),
    path('user-create/',CreateCustomUserView.as_view()),
    path('role-create/',RoleMasterCreateView.as_view()),
    path('approval/',ManagerApprovalView.as_view()),
    path('switch_role/',switch_role,name='switch_role'),
    path('search/',SerachView.as_view()),
    path('changepassword/',ChangePasswordView.as_view()),
    path('forgotpassword/',ForgotPasswordView.as_view()),
]