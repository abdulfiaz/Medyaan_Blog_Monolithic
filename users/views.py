from django.forms import model_to_dict
from django.contrib.auth.hashers import make_password,check_password
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import AllowAny
from rest_framework_jwt.serializers import jwt_payload_handler, jwt_encode_handler
from django.db import transaction
from users.models import *
from rest_framework.response import Response
from django.db import transaction
from rest_framework.views import APIView
from rest_framework import status
from django.conf import settings    
from users.serializers import *
from adminapp.iudetail import get_iuobj
from users.auth import get_user_roles,upload_image_s3
from django.template.loader import render_to_string
from notification.models import TemplateMaster,EventMaster
from adminapp.utils import get_notification
from django.core.mail import send_mail 
import random 
from sdd_blog.settings import EMAIL_HOST_USER


@api_view(['POST'])
@permission_classes([AllowAny, ])
def login(request):
    if request.method == 'POST':
        try:
            mobile_number = request.data['mobile_number']
            password = request.data['password']
 
            try:
                user = CustomUser.objects.get(mobile_number =mobile_number,is_active=True)
            except CustomUser.DoesNotExist:
                return Response({'status': 'error', 'message': 'Email / mobile number not found'}, status=status.HTTP_401_UNAUTHORIZED)
 
            if not check_password(password, user.password):
                return Response({'status': 'error', 'message': 'Incorrect Password'}, status=status.HTTP_401_UNAUTHORIZED)

            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
                    
            message = 'Login successfull'
            response_data = {'status': 'success', 'message': message, 'token': token}

            return Response({'status' : 'success' , 'message' : response_data})
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            transaction.rollback()
            return Response({'status': 'error', 'message': 'Something went wrong...' + str(e)},status=status.HTTP_400_BAD_REQUEST)
@api_view(['Post'])
def switch_role(request):
    if request.method == 'POST':
        try:
            transaction.set_autocommit(False)
            user=request.user
            domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
            iu_obj = get_iuobj(domain)
            if not iu_obj:
                return Response({'status': 'error', 'message': 'UNAUTHORIZED DOMAIN.'},status=status.HTTP_404_NOT_FOUND)
            role_id=request.data.get('role_id')
            role=RoleMaster.objects.get(id=role_id,is_active=True,iu_id=iu_obj)
            
            
            try:
                user_role=RoleMapping.objects.get(user=user,role=role,iu_id=iu_obj)
            except RoleMapping.DoesNotExist:
                transaction.rollback()
                return Response({"status":"error","message":f"You are not approved for role {role.name}"},status=status.HTTP_400_BAD_REQUEST)

            user.last_login_role=role.name
            user.save()
            payload = jwt_payload_handler(user)
            token = jwt_encode_handler(payload)
            transaction.commit()
            return Response({"status":"success","message":token},status=status.HTTP_200_OK)
        except Exception as e:
            transaction.rollback()
            return Response({"status":"error","message":str(e)},status=status.HTTP_400_BAD_REQUEST)

class RoleMasterCreateView(APIView):
    def post(self, request):
        try:
            user = request.user

            role_name_input = request.data.get('name')
            description = request.data.get('description')

            role_name = get_user_roles(request)

            if role_name != 'admin':
                return Response({'status': 'failure', 'message': 'Only admin users can create roles.'},status=status.HTTP_403_FORBIDDEN )

            if not role_name_input:
                return Response({'status': 'error', 'message': 'Role name is required.'},status=status.HTTP_400_BAD_REQUEST)

            try:
                domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
            except Exception as domain_error:
                domain = settings.APPLICATION_HOST

            iu_id = get_iuobj(domain)
    
            if not iu_id:
                return Response({'status': 'failure', 'message': 'IU domain not found.'},status=status.HTTP_404_NOT_FOUND)

            role = RoleMaster(
                name=role_name_input,
                description=description,
                iu_id=iu_id,
                created_by=request.user.id
            )
            role.save()

            return Response({'status': 'success', 'message': 'Role created successfully.', 'role_id': role.id},status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class CreateCustomUserView(APIView):
    def get(self, request):
        user=request.user
        role_name = request.query_params.get('role_name', None)

        user_role = get_user_roles(request)
        
        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)

        iu_obj = get_iuobj(domain)

        if not iu_obj:
            return Response({'status': 'failure', 'message': 'IU domain not found.'},status=status.HTTP_404_NOT_FOUND)

        if user_role in ['manager','admin'] and role_name is not None:
            if role_name == 'manager' and user_role != 'admin':
                return Response({'status':'error','message':"You are unauthorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)

            users = CustomUser.objects.filter(custom_user__role__name=role_name,iu_id = iu_obj,is_active=True)
        else:
            users = CustomUser.objects.filter(id=user.id,iu_id = iu_obj,is_active=True)
        user_data = GetCustomUserSerializer(users, many=True)
        return Response({"users": user_data.data}, status=status.HTTP_200_OK)
        
    def post(self, request):
        role_name = request.data.get('role_type', 'consumer')
        user_role = get_user_roles(request)
        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)

        iu_obj = get_iuobj(domain)

        if not iu_obj:
            return Response({'status': 'failure', 'message': 'UNAUTHORIZED DOMAIN.'},status=status.HTTP_404_NOT_FOUND)
        
        if user_role is None:
            role_name = 'consumer'
            
        elif user_role == 'consumer' and role_name in['publisher','eventorganiser'] :
            transaction.set_autocommit(False)      
            data=request.data
            data['user']=request.user.id
            data['created_by']=request.user.id
            data['iu_id']=iu_obj.id
                        # user role mapping for publisher-->>
            role = RoleMaster.objects.get(name=role_name)
            publisher_prof=PublisherProfile.objects.filter(is_active=True,user=request.user,role_type=role.name,is_rejected=False)
            if publisher_prof.exists():
                return Response({"status":"error","message":f"You were already an {role_name} account"},status=status.HTTP_400_BAD_REQUEST)
            
            serializer=PublisherProfileSerializer(data=data)
            if not serializer.is_valid():
                return Response({"status":"success","message":serializer.errors},status=status.HTTP_403_FORBIDDEN)                
            serializer.save()

            try:
                rolemap = RoleMapping.objects.get(user=request.user, role=role, iu_id=iu_obj)
            except RoleMapping.DoesNotExist:
                rolemap = RoleMapping(user=request.user, role=role, iu_id=iu_obj)
                rolemap.save()
            transaction.commit()
            return Response({"status":"success","message": f"{role_name} created successfully!"}, status=status.HTTP_201_CREATED)
        
        elif user_role != 'admin' and role_name == 'manager':
            return Response({"status":"error","message":"only admin can create manager and eventorganiser !"},status=status.HTTP_401_UNAUTHORIZED)
        
        transaction.set_autocommit(False)
        data=request.data
        data['iu_id']=iu_obj.id

        serializer = CustomUserSerializer(data=data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        if user_role:
            user.created_by=request.user.id
            user.save()
        else:
            user.created_by=user.id 
            user.save()
            
        try:
            role = RoleMaster.objects.get(name=role_name)
        except RoleMaster.DoesNotExist:
            transaction.rollback()
            return Response({"status":"error","message": "Role does not exist."},status=status.HTTP_400_BAD_REQUEST)

        rolemap = RoleMapping(user=user, role=role, iu_id=iu_obj)
        rolemap.save()

        data_user = request.data

        
        data_user['iu_id']= iu_obj.id
        data_user['user']= user.id
        data_user['created_by']= user.id 
        

        user_profile_serializer = UserPersonalProfileSerializer(data=data_user)
        if user_profile_serializer.is_valid():
            user_profile_serializer.save()
            transaction.commit()
            return Response({"status":"success","message": "User created successfully!"}, status=status.HTTP_201_CREATED)
        else:
            transaction.rollback()
            return Response(user_profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
             
    def put(self, request):
        
        data = request.data
        data['modified_by']=request.user.id
        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)

        iu_obj = get_iuobj(domain)

        if not iu_obj:
            return Response({'status': 'error', 'message': 'UNAUTHORIZED DOMAIN.'},status=status.HTTP_404_NOT_FOUND)
        
        user_role = get_user_roles(request)
        
        try:
            user = CustomUser.objects.get(id=request.user.id,iu_id=iu_obj,is_active=True)
        except CustomUser.DoesNotExist:
            return Response({"status":"success","message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        transaction.set_autocommit(False)

        user_serializer = CustomUserSerializer(user, data=data, partial=True)

        if not user_serializer.is_valid():
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user_serializer.save()     
        try:
            user_profile = UserPersonalProfile.objects.get(user=user,iu_id=iu_obj)
            
            user_profile_serializer = UserPersonalProfileSerializer(user_profile, data=data, partial=True)
            if not user_profile_serializer.is_valid():
                transaction.rollback()
                return Response(user_profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            user_profile_serializer.save()
            if user_role in ['publisher','eventorganiser']:
                publisher_detail=PublisherProfile.objects.get(user=request.user,role_type=user_role,iu_id=iu_obj,approved_status='approved',is_active=True)
                data['approved_status']='pending'
                serializer=PublisherProfileSerializer(publisher_detail,data=data,partial=True)
                if not serializer.is_valid():
                    return Response({"status":"error","message":serializer.errors},status=status.HTTP_400_BAD_REQUEST)
                serializer.save()
            
            transaction.commit()
            return Response({"status":"sucess","message": "User updated successfully!"},status=status.HTTP_200_OK)
        except PublisherProfile.DoesNotExist:
            transaction.rollback()
            return Response({"status":"error","message":f"{user_role} does not found"},status=status.HTTP_400_BAD_REQUEST)
        except UserPersonalProfile.DoesNotExist:
            return Response({"status":"error","message": "User personal profile not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_400_BAD_REQUEST)
   
    def delete(self, request):
        user_id = request.data.get('user_id',None)
        user_role = get_user_roles(request)
        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
        iu_obj = get_iuobj(domain)

        if user_id is not None and user_role in ['admin', 'manager'] :
            return Response({'status':'error','message':"you are unauthorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)
        else:
            user_id = request.user.id
        try:
            user = CustomUser.objects.get(id=user_id, iu_id=iu_obj,is_active=True)
            user_profile = UserPersonalProfile.objects.get(user=user, iu_id=iu_obj,is_active=True)
        except CustomUser.DoesNotExist:
            return Response({"status": "error", "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        user_role = RoleMapping.objects.get(user=user).role.name
        if user_role != 'consumer' and user_role == 'manager':
            return Response({"status": "error", "message": "you are unauthorized to do this action!"}, status=status.HTTP_401_UNAUTHORIZED)
        data={'is_active': False,'modified_by':request.user.id}
        user_serializer = CustomUserSerializer(user, data=data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_profile_serializer = UserPersonalProfileSerializer(user_profile, data={'is_active': False,'modified_by':request.user.id}, partial=True)
        if user_profile_serializer.is_valid():
            user_profile_serializer.save()
            return Response({"status": "success", "message": "User deleted successfully"}, status=status.HTTP_200_OK)
        else:
            return Response(user_profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# manager approval for publisher and eventorganiser
class ManagerApprovalView(APIView):
    def get(self,request):
        role_type = request.query_params.get('role_type')
        approved_status = request.query_params.get('approved_status')
        user_role = get_user_roles(request)
        
        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)

        iu_obj = get_iuobj(domain)

        if user_role != 'manager':
            return Response({"status":"error","message":"You are unaithorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)

        if not iu_obj:
            return Response({'status': 'failure', 'message': 'Unauthorized domain'},status=status.HTTP_404_NOT_FOUND)
        
        # to count the total of aproved_status'pending,approved,rejected' and total of all publisher,eventorganiser
        counts={}
        if approved_status is None:
            users = PublisherProfile.objects.filter(role_type=role_type,iu_id = iu_obj,is_active=True)
        elif approved_status == 'pending':
            users = PublisherProfile.objects.filter(role_type=role_type,approved_status='pending',iu_id=iu_obj,is_rejected=False,is_active=True)
        elif approved_status == 'approved':
            users = PublisherProfile.objects.filter(role_type=role_type,approved_status='approved',iu_id=iu_obj,is_rejected=False,is_active=True)
        elif approved_status == 'rejected':
            users = PublisherProfile.objects.filter(role_type=role_type,approved_status='rejected',iu_id=iu_obj,is_rejected=True,is_active=True)
        
        all_data= PublisherProfile.objects.filter(role_type=role_type, iu_id=iu_obj, is_active=True)
        counts['total_' + role_type] = all_data.count()
        counts['approved_status_pending'] = all_data.filter( approved_status='pending',is_rejected=False).count()
        counts['approved_status_approved'] = all_data.filter(approved_status='approved', is_rejected=False).count()
        counts['approved_status_rejected'] = all_data.filter(approved_status='rejected', is_rejected=True).count()
    

        user_data = GetPublisherProfileSerializer(users, many=True)
        return Response({"status":"success","message":"data retrieved successfully","data": user_data.data,"counts": counts}, status=status.HTTP_200_OK)

    def put(self,request):
        user_id = request.data.get('profile_id')
        
        user_role = get_user_roles(request)
        
        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
        iu_obj = get_iuobj(domain)
        if not iu_obj:
            return Response({'status': 'error', 'message': 'Unauthorized domain'},status=status.HTTP_401_UNAUTHORIZED)
        
        if user_role != 'manager':
            return Response({"status":"error","message":"You are unaithorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)
        
        if not user_id:
            return Response({"status":"error","message":"user_id is required"},status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = PublisherProfile.objects.get(id=user_id,approved_status='pending',is_active=True,iu_id=iu_obj)
        except PublisherProfile.DoesNotExist:
            return Response({"status":"error","message":"user not found!"},status=status.HTTP_404_NOT_FOUND)
        
        transaction.set_autocommit(False)
        data=request.data
        data['modified_by']=request.user.id
        if data['approved_status']== 'rejected':
            data['is_rejected']=True
        
        serializer=PublisherProfileSerializer(user,data=data,partial=True)
        
        if not serializer.is_valid():
            transaction.rollback()
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        
        user_data=model_to_dict(user)
        
        approved_status=request.data.get("approved_status")
        
        if approved_status =="approved":
            approved_profiles=ApprovedProfileSerializer(data=user_data)
            if not approved_profiles.is_valid():
                transaction.rollback()
                return Response(approved_profiles.errors, status=status.HTTP_400_BAD_REQUEST)
            approved_profiles.save()
       
        # template and email sending
        try:
            template=TemplateMaster.objects.get(template_name='manager_approve/reject_user')
        except Exception as e:
            return Response({"status":"error","message":"template does not exist"},status=status.HTTP_400_BAD_REQUEST)
        
        event=EventMaster.objects.get(name=template.template_name,iu_id=iu_obj,is_active=True)
        
        # template_message=template.content.format(user.id,request.user.id)
        message=f"your application for {user.role_type}"
        content={
            "approved_status":approved_status,
            "role":user.role_type,
            "message":message,
            "application_id":user.id,
            "manager_id":request.user.id
        }
                   
        rendered_html_message = render_to_string('profile_approving.html',content)
        
        sender_id=request.user.id
        receiver_id=user.user.id
        subject="Status of your application"
        
        email_id=user.user.email
        email_message=rendered_html_message
        role=event.role
        iu_id=iu_obj.id
        
        notification_data=get_notification(message,event,sender_id,receiver_id,subject,email_id,email_message,role,iu_id)
        if notification_data != 1:
            transaction.rollback()
            print(notification_data)
        transaction.commit()
        return Response({"status":"success","message":"User details updated successfully"},status=status.HTTP_200_OK)
    
# admin search users 
class SerachView(APIView):
    def get(self,request):
        email = request.query_params.get('email')
        search = request.query_params.get('search')
        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
        iu_obj = get_iuobj(domain)

        if not iu_obj:
            return Response({'status': 'failure', 'message': 'IU domain not found.'},status=status.HTTP_404_NOT_FOUND)
        
        user_role = get_user_roles(request)
        
        if user_role != 'admin':
            return Response({"status":"error","message":"You are unauthorized to do this action !"},status=status.HTTP_401_UNAUTHORIZED)
        
        if email:
            try:
                user_obj = CustomUser.objects.filter(email__istartswith=email,is_active=True,iu_id=iu_obj)
                serializer = GetCustomUserSerializer(user_obj,many=True)
                return Response({"status": "success","message":"Data retrived successfully","data": serializer.data}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        try:
            if search.isdigit():
                user_obj = CustomUser.objects.filter(mobile_number__startswith=search, is_active=True,iu_id=iu_obj)
            else:
                user_obj = CustomUser.objects.filter(userdetails__firstname__istartswith=search ,is_active=True,iu_id=iu_obj)
                
        except Exception as e:
            return Response({"status": "error", "message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  

        serializer = GetCustomUserSerializer(user_obj,many=True)    
        return Response({"status": "success","message":"Data retrived successfully","data": serializer.data}, status=status.HTTP_200_OK)

# change password
class ChangePasswordView(APIView):
    def put(self,request):
        try:
            old_password=request.data.get('old_password')
            new_password=request.data.get('new_password')
            confirm_password=request.data.get('confirm_password')

            domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
            iu_obj = get_iuobj(domain)
            if not iu_obj:
                return Response({'status': 'error', 'message': 'Unauthorized domain'},status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                user_obj=CustomUser.objects.get(id=request.user.id,is_active=True,iu_id=iu_obj)
            except CustomUser.DoesNotExist:
                return Response({"status":"error","message":"user not exists"},status=status.HTTP_404_NOT_FOUND)

            if not check_password(old_password,user_obj.password):
                return Response({"status":"error","message":"Old password doesnt match!"},status=status.HTTP_400_BAD_REQUEST)
            
            if new_password != confirm_password:
                return Response({"status":"error","message":"Password doesnt match!"},status=status.HTTP_400_BAD_REQUEST)
            
            user_obj.password=make_password(new_password)
            user_obj.temp_code=None
            user_obj.modified_by=request.user.id
            user_obj.save()
            return Response({"status":"success","message":"Password changed successfull"},status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_400_BAD_REQUEST)
            
# forgot password
class ForgotPasswordView(APIView):
    def post(self,request):
        try:
            email=request.data.get('email')
            
            domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
            iu_obj = get_iuobj(domain)
            if not iu_obj:
                return Response({'status': 'error', 'message': 'Unauthorized domain'},status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                user_obj=CustomUser.objects.get(email=email,is_active=True,iu_id=iu_obj)
            except CustomUser.DoesNotExist:
                return Response({"status":"error","message":"user not exists"},status=status.HTTP_404_NOT_FOUND)
            
            otp=str(random.randint(100000,999999))
            user_obj.temp_code=otp
            subject="Forgot poassword otp"
            body=f"Your otp is {otp}. This is valid upto 10 mins!"
            
            send_mail(subject,body,EMAIL_HOST_USER,[email])
            user_obj.save()
            return Response({"status":"sucess","message":"otp sent sucessfully"},status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_400_BAD_REQUEST)
        
    def put(self,request):
        try:
            email=request.data.get('email')
            new_password=request.data.get('new_password')
            confirm_password=request.data.get('confirm_password')
            otp=request.data.get('otp')

            domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
            iu_obj = get_iuobj(domain)
            if not iu_obj:
                return Response({'status': 'error', 'message': 'Unauthorized domain'},status=status.HTTP_401_UNAUTHORIZED)
            
            try:
                user_obj=CustomUser.objects.get(email=email,is_active=True,iu_id=iu_obj)
            except CustomUser.DoesNotExist:
                return Response({"status":"error","message":"user not exists"},status=status.HTTP_404_NOT_FOUND)
            
            if user_obj.temp_code != otp:
                return Response({"status":"error","message":"OTP is wrong!"},status=status.HTTP_400_BAD_REQUEST)
            
            if new_password != confirm_password:
                return Response({"status":"error","message":"Password doesnt match!"},status=status.HTTP_400_BAD_REQUEST)
            
            subject="Password changed!"
            body=f"Your new password has been updated successfuly!"

            user_obj.password=make_password(new_password)
            user_obj.temp_code=None
            send_mail(subject,body,EMAIL_HOST_USER,[email])
            user_obj.save()
            return Response({"status":"success","message":"Password updated successfully"},status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"status":"error","message":str(e)},status=status.HTTP_400_BAD_REQUEST)




        



        


        
        

