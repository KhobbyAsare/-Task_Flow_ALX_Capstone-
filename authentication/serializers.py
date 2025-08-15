from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator
from django.contrib.auth import authenticate
from .models import UserProfile


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    """
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True, 
        required=True, 
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password_confirm', 'email', 
                 'first_name', 'last_name')

    def validate(self, attrs):
        """
        Validate that password and password_confirm match
        """
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        return attrs

    def validate_username(self, value):
        """
        Validate username uniqueness and format
        """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )
        return value

    def create(self, validated_data):
        """
        Create and return a new user instance
        """
        # Remove password_confirm from validated_data
        validated_data.pop('password_confirm', None)
        
        # Create user
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        return user


class EmailLoginSerializer(serializers.Serializer):
    """
    Serializer for email-based login
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            # Try to find user by email
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError(
                    'No account found with this email address.'
                )
            
            # Authenticate using username (since Django's authenticate expects username)
            user = authenticate(username=user.username, password=password)
            
            if not user:
                raise serializers.ValidationError(
                    'Invalid email or password.'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    'User account is disabled.'
                )
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                'Must include email and password.'
            )


class ExtendedUserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for the extended UserProfile model
    """
    class Meta:
        model = UserProfile
        fields = ('bio', 'phone_number', 'birth_date', 'location', 'website', 
                 'profile_picture', 'is_profile_public', 'show_email')


class UserDataSerializer(serializers.ModelSerializer):
    """
    Serializer for getting complete user data (read-only)
    """
    profile = ExtendedUserProfileSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    profile_picture_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                 'date_joined', 'last_login', 'is_active', 'full_name', 
                 'profile_picture_url', 'profile')
        read_only_fields = ('id', 'username', 'date_joined', 'last_login', 
                          'is_active', 'full_name', 'profile_picture_url')
    
    def get_full_name(self, obj):
        """Get user's full name"""
        return f"{obj.first_name} {obj.last_name}".strip()
    
    def get_profile_picture_url(self, obj):
        """Get profile picture URL"""
        if hasattr(obj, 'profile') and obj.profile.profile_picture:
            return obj.profile.profile_picture.url
        return '/static/images/default-avatar.png'


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user basic information
    """
    email = serializers.EmailField(required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    
    # Profile fields
    bio = serializers.CharField(max_length=500, required=False, allow_blank=True)
    phone_number = serializers.CharField(max_length=15, required=False, allow_blank=True)
    birth_date = serializers.DateField(required=False, allow_null=True)
    location = serializers.CharField(max_length=100, required=False, allow_blank=True)
    website = serializers.URLField(required=False, allow_blank=True)
    profile_picture = serializers.ImageField(required=False, allow_null=True)
    is_profile_public = serializers.BooleanField(required=False)
    show_email = serializers.BooleanField(required=False)
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'bio', 'phone_number', 
                 'birth_date', 'location', 'website', 'profile_picture', 
                 'is_profile_public', 'show_email')
    
    def validate_email(self, value):
        """Validate email uniqueness (excluding current user)"""
        user = self.instance
        if User.objects.filter(email=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value
    
    def update(self, instance, validated_data):
        """Update user and profile information"""
        # Extract profile fields
        profile_fields = {
            'bio': validated_data.pop('bio', None),
            'phone_number': validated_data.pop('phone_number', None),
            'birth_date': validated_data.pop('birth_date', None),
            'location': validated_data.pop('location', None),
            'website': validated_data.pop('website', None),
            'profile_picture': validated_data.pop('profile_picture', None),
            'is_profile_public': validated_data.pop('is_profile_public', None),
            'show_email': validated_data.pop('show_email', None),
        }
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update profile fields
        if hasattr(instance, 'profile'):
            profile = instance.profile
            for attr, value in profile_fields.items():
                if value is not None:
                    setattr(profile, attr, value)
            profile.save()
        
        return instance


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile (backward compatibility)
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_joined')
        read_only_fields = ('id', 'username', 'date_joined')
