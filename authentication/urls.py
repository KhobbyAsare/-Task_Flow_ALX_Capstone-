from django.urls import path
from .views import UserRegistrationView, UserProfileView, EmailLoginView, LogoutView

urlpatterns = [
    # User registration
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    
    # User login with email and password
    path('login/', EmailLoginView.as_view(), name='user-login'),
    
    # User logout
    path('logout/', LogoutView.as_view(), name='user-logout'),
    
    # User profile
    path('profile/', UserProfileView.as_view(), name='user-profile'),
]
