from django.urls import path
from .views import (
    UserRegistrationView, 
    UserProfileView, 
    EmailLoginView, 
    LogoutView,
    UserDataView,
    UserUpdateView
)

urlpatterns = [
    # User registration
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    
    # User login with email and password
    path('login/', EmailLoginView.as_view(), name='user-login'),
    
    # User logout
    path('logout/', LogoutView.as_view(), name='user-logout'),
    
    # User profile (legacy endpoint for backward compatibility)
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    
    # New dedicated endpoints
    # Get complete user data
    path('user-data/', UserDataView.as_view(), name='user-data'),
    
    # Update user data
    path('user-update/', UserUpdateView.as_view(), name='user-update'),
]
