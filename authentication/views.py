from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.conf import settings
from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    EmailLoginSerializer,
    UserDataSerializer,
    UserUpdateSerializer
)


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        user_serializer = UserProfileSerializer(user)
        
        return Response({
            'message': 'User registered successfully',
            'user': user_serializer.data,
            'token': token.key
        }, status=status.HTTP_201_CREATED)


class EmailLoginView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = EmailLoginSerializer
    
    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer()
        return Response({
            'message': 'Please provide email and password to login',
            'required_fields': {
                'email': 'Your email address',
                'password': 'Your password'
            }
        })
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            token, created = Token.objects.get_or_create(user=user)
            user_serializer = UserProfileSerializer(user)
            
            return Response({
                'message': 'Login successful',
                'user': user_serializer.data,
                'token': token.key
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    
    def get_object(self):
        return self.request.user


class UserDataView(generics.RetrieveAPIView):
    serializer_class = UserDataSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'message': 'User data retrieved successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class UserUpdateView(generics.UpdateAPIView):
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        self.perform_update(serializer)
        updated_user_serializer = UserDataSerializer(instance)
        
        return Response({
            'message': 'User data updated successfully',
            'data': updated_user_serializer.data
        }, status=status.HTTP_200_OK)
    
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        try:
            try:
                token = Token.objects.get(user=request.user)
                token.delete()
            except Token.DoesNotExist:
                pass
            
            logout(request)
            
            content_type = request.content_type
            has_auth_header = 'Authorization' in request.headers
            is_api_request = (content_type and 'application/json' in content_type) or has_auth_header
            
            if is_api_request:
                return Response({
                    'message': 'Logout successful'
                }, status=status.HTTP_200_OK)
            else:
                return redirect(settings.LOGIN_URL)
            
        except Exception as e:
            if 'application/json' in request.content_type:
                return Response({
                    'message': 'Logout completed with minor issues'
                }, status=status.HTTP_200_OK)
            else:
                return redirect(settings.LOGIN_URL)
    
    def get(self, request, *args, **kwargs):
        accept_header = request.headers.get('Accept', '')
        is_browser_request = 'text/html' in accept_header
        
        if is_browser_request:
            logout(request)
            return redirect(settings.LOGIN_URL)
        else:
            return Response({
                'message': 'Send a POST request to this endpoint to logout',
                'user': request.user.username if request.user.is_authenticated else 'Anonymous'
            })


class WebLogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect(settings.LOGIN_URL)
    
    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect(settings.LOGIN_URL)
