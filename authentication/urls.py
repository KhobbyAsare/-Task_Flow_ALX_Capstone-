from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token
from .views import UserRegistrationView, UserProfileView

urlpatterns = [
    # User registration
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    
    # User login (get token)
    path('login/', obtain_auth_token, name='user-login'),
    
    # User profile
    path('profile/', UserProfileView.as_view(), name='user-profile'),
]
