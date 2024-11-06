from django.shortcuts import render
from django.contrib.auth.hashers import make_password,check_password
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_jwt.serializers import jwt_payload_handler, jwt_encode_handler
from django.db import transaction, IntegrityError
from users.models import *
from rest_framework.response import Response
from django.db import transaction
from rest_framework.views import APIView
from rest_framework import status
from django.db.models import QuerySet
from django.conf import settings    
from users.serializers import CustomUserSerializer, UserPersonalProfileSerializer,GetCustomUserSerializer
from adminapp.iudetail import get_iuobj
from users.auth import get_user_roles
from rest_framework.exceptions import AuthenticationFailed
from django.shortcuts import get_object_or_404


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

        iu_master = get_iuobj(domain)

        if not iu_master:
            return Response({'status': 'failure', 'message': 'IU domain not found.'},status=status.HTTP_404_NOT_FOUND)

        if user_role in ['manager','admin'] and role_name is not None:
            if role_name == 'manager' and user_role != 'admin':
                return Response({'status':'error','message':"You are unauthorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)

            users = CustomUser.objects.filter(custom_user__role__name=role_name,iu_id = iu_master,is_active=True)
        else:
            users = CustomUser.objects.filter(id=user.id,iu_id = iu_master,is_active=True)
        user_data = GetCustomUserSerializer(users, many=True)
        return Response({"users": user_data.data}, status=status.HTTP_200_OK)
        
    def post(self, request):
        role_name = request.data.get('role_name', 'consumer')
        user_role = get_user_roles(request)

        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)

        iu_master = get_iuobj(domain)

        if not iu_master:
            return Response({'status': 'failure', 'message': 'IU domain not found.'},status=status.HTTP_404_NOT_FOUND)
        
        if user_role is None:
            role_name = 'consumer'
            
        elif user_role != 'admin' and role_name in ['manager','eventorganizer']:
            return Response({"status":"error","message":"only admin can create manager and eventorganiser !"},status=status.HTTP_401_UNAUTHORIZED)
        elif user_role == 'consumer' and role_name == 'publisher' :
                # logics
            return Response({"status":"success","message": "Publisher created successfully!"}, status=status.HTTP_201_CREATED)
        elif user_role == 'consumer' and role_name == 'eventorganizer':
                # logics
            return Response({"status":"success","message": "eventorganizer created successfully!"}, status=status.HTTP_201_CREATED)

        transaction.set_autocommit(False)
        data=request.data
        data['iu_id']=iu_master.id

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

        rolemap = RoleMapping(user=user, role=role, iu_id=iu_master)
        rolemap.save()

        data_user = request.data

        
        data_user['iu_id']= iu_master.id
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

        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)

        iu_master = get_iuobj(domain)

        if not iu_master:
            return Response({'status': 'error', 'message': 'IU domain not found.'},status=status.HTTP_404_NOT_FOUND)

        try:
            user = CustomUser.objects.get(id=request.user.id,iu_id=iu_master,is_active=True)
        except CustomUser.DoesNotExist:
            return Response({"status":"success","message": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        
        transaction.set_autocommit(False)
        data =request.data
        data['modified_by']=request.user.id

        user_serializer = CustomUserSerializer(user, data=data, partial=True)

        if user_serializer.is_valid():
            user_serializer.save()
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_profile = UserPersonalProfile.objects.get(user=user,iu_id=iu_master)
        except UserPersonalProfile.DoesNotExist:
            return Response({"status":"error","message": "User personal profile not found."}, status=status.HTTP_404_NOT_FOUND)
        
        data =request.data
        data['modified_by']=request.user.id
        user_profile_serializer = UserPersonalProfileSerializer(user_profile, data=data, partial=True)
        
        
        if user_profile_serializer.is_valid():
            user_profile_serializer.save()
            transaction.commit()
            return Response({"status":"sucess","message": "User updated successfully!"}, status=status.HTTP_200_OK)
        
        else:
            transaction.rollback()
            return Response(user_profile_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
   
    def delete(self, request):
        user_id = request.data.get('user_id',None)
        user_role = get_user_roles(request)
        domain = request.META.get('HTTP_ORIGIN', settings.APPLICATION_HOST)
        iu_master = get_iuobj(domain)

        if user_role not in ['admin', 'manager'] :
            return Response({'status':'error','message':"you are unauthorized to do this action!"},status=status.HTTP_401_UNAUTHORIZED)

        try:
            user = CustomUser.objects.get(id=user_id, iu_id=iu_master,is_active=True)
            user_profile = UserPersonalProfile.objects.get(user=user, iu_id=iu_master,is_active=True)
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

