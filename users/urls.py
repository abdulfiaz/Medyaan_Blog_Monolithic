from django.conf.urls import url
from django.urls import path
from users import views
from users.views import RoleMasterCreateView,CreateCustomUserView

app_name = 'users'

urlpatterns = [
    path('login/', views.login, name='login'),
    path('user-create/',CreateCustomUserView.as_view()),
    path('role-create/',RoleMasterCreateView.as_view()),
]