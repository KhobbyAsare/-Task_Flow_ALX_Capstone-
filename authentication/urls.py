from django.urls import path
from .views import (
    UserRegistrationView, 
    UserProfileView, 
    EmailLoginView, 
    LogoutView,
    WebLogoutView,
    UserDataView,
    UserUpdateView
)

urlpatterns = [
    # User registration
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    
    # User login with email and password
    path('login/', EmailLoginView.as_view(), name='user-login'),
    
    # User logout (API)
    path('logout/', LogoutView.as_view(), name='user-logout'),
    
    # Web logout (always redirects)
    path('web-logout/', WebLogoutView.as_view(), name='web-logout'),
    
    # User profile
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    
    # Get complete user data
    path('user-data/', UserDataView.as_view(), name='user-data'),
    
    # Update user data
    path('user-update/', UserUpdateView.as_view(), name='user-update'),
]
