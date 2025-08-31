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
    """
    API endpoint for user registration
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]  # Allow anyone to register

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create the user
        user = serializer.save()
        
        # Create token for the user
        token, created = Token.objects.get_or_create(user=user)
        
        # Return user data with token
        user_serializer = UserProfileSerializer(user)
        
        return Response({
            'message': 'User registered successfully',
            'user': user_serializer.data,
            'token': token.key
        }, status=status.HTTP_201_CREATED)


class EmailLoginView(generics.GenericAPIView):
    """
    API endpoint for email-based user login
    """
    permission_classes = [AllowAny]
    serializer_class = EmailLoginSerializer
    
    def get(self, request, *args, **kwargs):
        """
        Display the login form in browsable API
        """
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
            
            # Get or create token for the user
            token, created = Token.objects.get_or_create(user=user)
            
            # Return user data with token
            user_serializer = UserProfileSerializer(user)
            
            return Response({
                'message': 'Login successful',
                'user': user_serializer.data,
                'token': token.key
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API endpoint for viewing and updating user profile
    """
    serializer_class = UserProfileSerializer
    
    def get_object(self):
        return self.request.user


class UserDataView(generics.RetrieveAPIView):
    """
    API endpoint to get complete user data
    GET /auth/user-data/
    """
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
    """
    API endpoint to update user data
    PUT/PATCH /auth/user-update/
    """
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Perform the update
        self.perform_update(serializer)
        
        # Return updated user data
        updated_user_serializer = UserDataSerializer(instance)
        
        return Response({
            'message': 'User data updated successfully',
            'data': updated_user_serializer.data
        }, status=status.HTTP_200_OK)
    
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class LogoutView(APIView):
    """
    API endpoint for user logout
    Deletes the user's authentication token and handles both API and web requests
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        try:
            # Get the user's token and delete it (for API users)
            try:
                token = Token.objects.get(user=request.user)
                token.delete()
            except Token.DoesNotExist:
                pass  # No token to delete
            
            # Log out the user from Django's session system (for web users)
            logout(request)
            
            # Check if this is an API request (JSON content type or has Authorization header)
            content_type = request.content_type
            has_auth_header = 'Authorization' in request.headers
            is_api_request = (content_type and 'application/json' in content_type) or has_auth_header
            
            if is_api_request:
                return Response({
                    'message': 'Logout successful'
                }, status=status.HTTP_200_OK)
            else:
                # Web request - redirect to login page
                return redirect(settings.LOGIN_URL)
            
        except Exception as e:
            if 'application/json' in request.content_type:
                return Response({
                    'message': 'Logout completed with minor issues'
                }, status=status.HTTP_200_OK)
            else:
                return redirect(settings.LOGIN_URL)
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET requests - for web requests, redirect to login
        """
        # Check if this is likely a web browser request
        accept_header = request.headers.get('Accept', '')
        is_browser_request = 'text/html' in accept_header
        
        if is_browser_request:
            # Log out the user and redirect to login page
            logout(request)
            return redirect(settings.LOGIN_URL)
        else:
            # API request - return JSON response
            return Response({
                'message': 'Send a POST request to this endpoint to logout',
                'user': request.user.username if request.user.is_authenticated else 'Anonymous'
            })


class WebLogoutView(APIView):
    """
    Web-specific logout view that always redirects to login page
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET request for logout (typical web logout)
        """
        logout(request)
        return redirect(settings.LOGIN_URL)
    
    def post(self, request, *args, **kwargs):
        """
        Handle POST request for logout
        """
        logout(request)
        return redirect(settings.LOGIN_URL)
