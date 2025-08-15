from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.contrib.auth.models import User
from .serializers import UserRegistrationSerializer, UserProfileSerializer, EmailLoginSerializer


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
