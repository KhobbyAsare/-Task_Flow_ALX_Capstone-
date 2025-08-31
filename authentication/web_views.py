from django.contrib.auth import logout
from django.shortcuts import redirect
from django.conf import settings
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages


class CustomLogoutView(LoginRequiredMixin, View):
    """
    Custom logout view that handles both GET and POST requests
    and always redirects to the login page
    """
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET request for logout (typical web logout via link)
        """
        user = request.user
        logout(request)
        messages.success(request, f'You have been successfully logged out. See you next time!')
        return redirect(settings.LOGIN_URL)
    
    def post(self, request, *args, **kwargs):
        """
        Handle POST request for logout
        """
        user = request.user
        logout(request)
        messages.success(request, f'You have been successfully logged out. See you next time!')
        return redirect(settings.LOGIN_URL)
