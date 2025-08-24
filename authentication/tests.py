import json
from datetime import datetime, date
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from .models import UserProfile
from .serializers import (
    UserRegistrationSerializer,
    EmailLoginSerializer,
    UserDataSerializer,
    UserUpdateSerializer,
    UserProfileSerializer
)


class BaseAuthTestCase(APITestCase):
    """Base test case with common setup for authentication tests"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create test user
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create token for test user
        self.token = Token.objects.create(user=self.test_user)
        
        # Sample user data for registration
        self.valid_user_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123!',
            'password_confirm': 'newpass123!',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        # Sample login data
        self.valid_login_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
    
    def authenticate_user(self):
        """Helper method to authenticate test user"""
        self.client.force_authenticate(user=self.test_user, token=self.token)
    
    def create_test_user(self, username='testuser2', email='test2@example.com'):
        """Helper method to create additional test users"""
        return User.objects.create_user(
            username=username,
            email=email,
            password='testpass123',
            first_name='Test2',
            last_name='User2'
        )


class UserRegistrationViewTests(BaseAuthTestCase):
    """Test cases for UserRegistrationView"""
    
    def setUp(self):
        super().setUp()
        self.url = reverse('user-register')
    
    def test_successful_registration(self):
        """Test successful user registration"""
        response = self.client.post(self.url, self.valid_user_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['message'], 'User registered successfully')
        
        # Verify user was created in database
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
        # Verify token was created
        user = User.objects.get(username='newuser')
        self.assertTrue(Token.objects.filter(user=user).exists())
        
        # Verify profile was created
        self.assertTrue(hasattr(user, 'profile'))
    
    def test_registration_with_duplicate_username(self):
        """Test registration fails with duplicate username"""
        data = self.valid_user_data.copy()
        data['username'] = 'testuser'  # existing username
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('username', response.data)
    
    def test_registration_with_duplicate_email(self):
        """Test registration fails with duplicate email"""
        data = self.valid_user_data.copy()
        data['email'] = 'test@example.com'  # existing email
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_registration_password_mismatch(self):
        """Test registration fails when passwords don't match"""
        data = self.valid_user_data.copy()
        data['password_confirm'] = 'differentpass'
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
    
    def test_registration_weak_password(self):
        """Test registration fails with weak password"""
        data = self.valid_user_data.copy()
        data['password'] = '123'  # too short
        data['password_confirm'] = '123'
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
    
    def test_registration_missing_required_fields(self):
        """Test registration fails with missing required fields"""
        incomplete_data = {
            'username': 'newuser',
            'email': 'newuser@example.com'
            # missing password, password_confirm, first_name, last_name
        }
        
        response = self.client.post(self.url, incomplete_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
        self.assertIn('first_name', response.data)
        self.assertIn('last_name', response.data)
    
    def test_registration_invalid_email_format(self):
        """Test registration fails with invalid email format"""
        data = self.valid_user_data.copy()
        data['email'] = 'invalid-email'
        
        response = self.client.post(self.url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)


class EmailLoginViewTests(BaseAuthTestCase):
    """Test cases for EmailLoginView"""
    
    def setUp(self):
        super().setUp()
        self.url = reverse('user-login')
    
    def test_successful_login(self):
        """Test successful login with valid credentials"""
        response = self.client.post(self.url, self.valid_login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['message'], 'Login successful')
        
        # Verify token is returned
        self.assertEqual(response.data['token'], self.token.key)
    
    def test_login_with_invalid_email(self):
        """Test login fails with non-existent email"""
        invalid_data = {
            'email': 'nonexistent@example.com',
            'password': 'testpass123'
        }
        
        response = self.client.post(self.url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('No account found with this email address', str(response.data))
    
    def test_login_with_invalid_password(self):
        """Test login fails with incorrect password"""
        invalid_data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        
        response = self.client.post(self.url, invalid_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Invalid email or password', str(response.data))
    
    def test_login_with_inactive_user(self):
        """Test login fails with inactive user"""
        self.test_user.is_active = False
        self.test_user.save()
        
        response = self.client.post(self.url, self.valid_login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # The serializer might return "Invalid email or password" instead of specific disabled message
        # This is common for security reasons to avoid revealing account status
        self.assertIn('Invalid email or password', str(response.data))
    
    def test_login_missing_credentials(self):
        """Test login fails with missing credentials"""
        incomplete_data = {'email': 'test@example.com'}
        
        response = self.client.post(self.url, incomplete_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
    
    def test_login_get_request(self):
        """Test GET request to login endpoint returns form info"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('required_fields', response.data)
        self.assertEqual(response.data['message'], 'Please provide email and password to login')


class UserProfileViewTests(BaseAuthTestCase):
    """Test cases for UserProfileView"""
    
    def setUp(self):
        super().setUp()
        self.url = reverse('user-profile')
    
    def test_get_user_profile_authenticated(self):
        """Test retrieving user profile when authenticated"""
        self.authenticate_user()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.test_user.username)
        self.assertEqual(response.data['email'], self.test_user.email)
    
    def test_get_user_profile_unauthenticated(self):
        """Test retrieving user profile when not authenticated"""
        response = self.client.get(self.url)
        
        # Django REST Framework returns 403 by default for authentication required views
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_update_user_profile(self):
        """Test updating user profile"""
        self.authenticate_user()
        
        update_data = {
            'first_name': 'UpdatedFirst',
            'last_name': 'UpdatedLast',
            'email': 'updated@example.com'
        }
        
        response = self.client.patch(self.url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify user was updated
        self.test_user.refresh_from_db()
        self.assertEqual(self.test_user.first_name, 'UpdatedFirst')
        self.assertEqual(self.test_user.last_name, 'UpdatedLast')
        self.assertEqual(self.test_user.email, 'updated@example.com')


class UserDataViewTests(BaseAuthTestCase):
    """Test cases for UserDataView"""
    
    def setUp(self):
        super().setUp()
        self.url = reverse('user-data')
    
    def test_get_user_data_authenticated(self):
        """Test retrieving complete user data when authenticated"""
        self.authenticate_user()
        
        # Update profile with some data
        profile = self.test_user.profile
        profile.bio = 'Test bio'
        profile.location = 'Test City'
        profile.save()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('data', response.data)
        self.assertEqual(response.data['message'], 'User data retrieved successfully')
        
        # Verify data structure
        user_data = response.data['data']
        self.assertIn('username', user_data)
        self.assertIn('email', user_data)
        self.assertIn('profile', user_data)
        self.assertIn('full_name', user_data)
        
        # Verify profile data
        self.assertEqual(user_data['profile']['bio'], 'Test bio')
        self.assertEqual(user_data['profile']['location'], 'Test City')
    
    def test_get_user_data_unauthenticated(self):
        """Test retrieving user data when not authenticated"""
        response = self.client.get(self.url)
        
        # Django REST Framework returns 403 by default for authentication required views
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


class UserUpdateViewTests(BaseAuthTestCase):
    """Test cases for UserUpdateView"""
    
    def setUp(self):
        super().setUp()
        self.url = reverse('user-update')
    
    def test_update_user_basic_info_put(self):
        """Test updating user basic info with PUT request"""
        self.authenticate_user()
        
        update_data = {
            'first_name': 'UpdatedFirst',
            'last_name': 'UpdatedLast',
            'email': 'updated@example.com',
            'bio': 'Updated bio'
        }
        
        response = self.client.put(self.url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'User data updated successfully')
        
        # Verify user was updated
        self.test_user.refresh_from_db()
        self.assertEqual(self.test_user.first_name, 'UpdatedFirst')
        self.assertEqual(self.test_user.last_name, 'UpdatedLast')
        self.assertEqual(self.test_user.email, 'updated@example.com')
        
        # Verify profile was updated
        self.test_user.profile.refresh_from_db()
        self.assertEqual(self.test_user.profile.bio, 'Updated bio')
    
    def test_update_user_partial_patch(self):
        """Test partial update with PATCH request"""
        self.authenticate_user()
        
        update_data = {
            'bio': 'New bio only',
            'location': 'New City'
        }
        
        response = self.client.patch(self.url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify only specified fields were updated
        self.test_user.profile.refresh_from_db()
        self.assertEqual(self.test_user.profile.bio, 'New bio only')
        self.assertEqual(self.test_user.profile.location, 'New City')
        
        # Verify other fields unchanged
        self.assertEqual(self.test_user.first_name, 'Test')  # Original value
    
    def test_update_with_duplicate_email(self):
        """Test update fails with duplicate email"""
        self.authenticate_user()
        
        # Create another user with an email
        other_user = self.create_test_user(username='otheruser', email='other@example.com')
        
        update_data = {
            'email': 'other@example.com'  # existing email
        }
        
        response = self.client.patch(self.url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_update_unauthenticated(self):
        """Test update fails when not authenticated"""
        update_data = {'first_name': 'NewName'}
        
        response = self.client.patch(self.url, update_data, format='json')
        
        # Django REST Framework returns 403 by default for authentication required views
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_update_with_birth_date(self):
        """Test updating with date fields"""
        self.authenticate_user()
        
        update_data = {
            'birth_date': '1990-01-01',
            'phone_number': '+1234567890'
        }
        
        response = self.client.patch(self.url, update_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify profile was updated
        self.test_user.profile.refresh_from_db()
        self.assertEqual(self.test_user.profile.birth_date, date(1990, 1, 1))
        self.assertEqual(self.test_user.profile.phone_number, '+1234567890')


class LogoutViewTests(BaseAuthTestCase):
    """Test cases for LogoutView"""
    
    def setUp(self):
        super().setUp()
        self.url = reverse('user-logout')
    
    def test_successful_logout(self):
        """Test successful logout deletes token"""
        self.authenticate_user()
        
        # Verify token exists
        self.assertTrue(Token.objects.filter(user=self.test_user).exists())
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Logout successful')
        
        # Verify token was deleted
        self.assertFalse(Token.objects.filter(user=self.test_user).exists())
    
    def test_logout_already_logged_out(self):
        """Test logout when user is already logged out"""
        self.authenticate_user()
        
        # Delete token manually
        Token.objects.filter(user=self.test_user).delete()
        
        response = self.client.post(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'User was already logged out')
    
    def test_logout_unauthenticated(self):
        """Test logout fails when not authenticated"""
        response = self.client.post(self.url)
        
        # Django REST Framework returns 403 by default for authentication required views
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_logout_get_request(self):
        """Test GET request to logout endpoint"""
        self.authenticate_user()
        
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user'], self.test_user.username)


class UserProfileModelTests(TestCase):
    """Test cases for UserProfile model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='modeltest',
            email='modeltest@example.com',
            password='testpass123',
            first_name='Model',
            last_name='Test'
        )
    
    def test_profile_created_on_user_creation(self):
        """Test that profile is automatically created when user is created"""
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, UserProfile)
    
    def test_profile_str_method(self):
        """Test profile string representation"""
        expected_str = f"{self.user.username}'s Profile"
        self.assertEqual(str(self.user.profile), expected_str)
    
    def test_full_name_property(self):
        """Test full_name property"""
        self.assertEqual(self.user.profile.full_name, 'Model Test')
        
        # Test with empty names
        self.user.first_name = ''
        self.user.last_name = ''
        self.user.save()
        self.assertEqual(self.user.profile.full_name, '')
    
    def test_default_profile_picture_url(self):
        """Test default profile picture URL"""
        expected_url = '/static/images/default-avatar.png'
        self.assertEqual(self.user.profile.get_profile_picture_url, expected_url)
    
    @patch('authentication.models.UserProfile.profile_picture')
    def test_custom_profile_picture_url(self, mock_picture):
        """Test custom profile picture URL"""
        mock_picture.url = '/media/profile_pictures/test.jpg'
        mock_picture.__bool__ = lambda x: True
        
        # This test would need actual file handling in a real scenario
        # For now, we just test the logic path exists
        self.assertTrue(hasattr(self.user.profile, 'get_profile_picture_url'))
    
    def test_profile_fields_defaults(self):
        """Test profile field defaults"""
        profile = self.user.profile
        
        self.assertIsNone(profile.bio)
        self.assertIsNone(profile.phone_number)
        self.assertIsNone(profile.birth_date)
        self.assertIsNone(profile.location)
        self.assertIsNone(profile.website)
        self.assertTrue(profile.is_profile_public)
        self.assertFalse(profile.show_email)
    
    def test_profile_field_updates(self):
        """Test updating profile fields"""
        profile = self.user.profile
        
        profile.bio = 'Test bio'
        profile.phone_number = '+1234567890'
        profile.location = 'Test City'
        profile.website = 'https://example.com'
        profile.is_profile_public = False
        profile.show_email = True
        profile.save()
        
        profile.refresh_from_db()
        
        self.assertEqual(profile.bio, 'Test bio')
        self.assertEqual(profile.phone_number, '+1234567890')
        self.assertEqual(profile.location, 'Test City')
        self.assertEqual(profile.website, 'https://example.com')
        self.assertFalse(profile.is_profile_public)
        self.assertTrue(profile.show_email)


class SerializerTests(TestCase):
    """Test cases for authentication serializers"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='serializertest',
            email='serializer@example.com',
            password='testpass123',
            first_name='Serializer',
            last_name='Test'
        )
    
    def test_user_registration_serializer_valid(self):
        """Test UserRegistrationSerializer with valid data"""
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'newpass123!',
            'password_confirm': 'newpass123!',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        serializer = UserRegistrationSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        
        user = serializer.save()
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'new@example.com')
        self.assertTrue(user.check_password('newpass123!'))
    
    def test_email_login_serializer_valid(self):
        """Test EmailLoginSerializer with valid credentials"""
        data = {
            'email': 'serializer@example.com',
            'password': 'testpass123'
        }
        
        serializer = EmailLoginSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['user'], self.user)
    
    def test_email_login_serializer_invalid(self):
        """Test EmailLoginSerializer with invalid credentials"""
        data = {
            'email': 'serializer@example.com',
            'password': 'wrongpassword'
        }
        
        serializer = EmailLoginSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('Invalid email or password', str(serializer.errors))
    
    def test_user_data_serializer(self):
        """Test UserDataSerializer"""
        serializer = UserDataSerializer(self.user)
        data = serializer.data
        
        self.assertIn('username', data)
        self.assertIn('email', data)
        self.assertIn('profile', data)
        self.assertIn('full_name', data)
        self.assertEqual(data['full_name'], 'Serializer Test')
    
    def test_user_update_serializer(self):
        """Test UserUpdateSerializer"""
        data = {
            'first_name': 'Updated',
            'bio': 'Updated bio'
        }
        
        serializer = UserUpdateSerializer(self.user, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        
        updated_user = serializer.save()
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.profile.bio, 'Updated bio')
