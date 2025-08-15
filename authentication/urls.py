from django.urls import path
from .views import UserRegistrationView, UserProfileView, EmailLoginView

urlpatterns = [
    # User registration
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    
    # User login with email and password
    path('login/', EmailLoginView.as_view(), name='user-login'),
    
    # User profile
    path('profile/', UserProfileView.as_view(), name='user-profile'),
]
