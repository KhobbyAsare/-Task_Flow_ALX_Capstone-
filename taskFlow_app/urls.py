"""
URL configuration for taskFlow_app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from authentication.web_views import CustomLogoutView
from task.dashboard_views import register_view

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Web interface URLs
    path('', include(('task.urls', 'task'), namespace='web')),  # Dashboard and web views
    path('auth/', include(('authentication.urls', 'auth'), namespace='web_auth')),  # Authentication
    
    # API URLs (existing)
    path('api/auth/', include(('authentication.urls', 'auth'), namespace='api_auth')),
    path('api/tasks/', include(('task.urls', 'task'), namespace='api')),
    path('api/', include('rest_framework.urls')),  # DRF browsable API
    
    # Django built-in authentication for web views
    path('accounts/login/', LoginView.as_view(), name='login'),
    path('accounts/logout/', CustomLogoutView.as_view(), name='logout'),
    path('accounts/password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('accounts/password_reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('accounts/reset/done/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('accounts/register/', register_view, name='register'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
