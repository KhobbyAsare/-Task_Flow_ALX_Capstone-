from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework.validators import UniqueValidator


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


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile (read-only)
    """
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'date_joined')
        read_only_fields = ('id', 'username', 'date_joined')
