from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from organization.models import Organization
import re
from django.db.models import Q

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    username = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    organization_code = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone', 'organization_code'
        ]
    
    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("Username already exists")
        
        # Username validation rules
        if not re.match(r'^[a-zA-Z0-9_]+$', value):
            raise serializers.ValidationError("Username can only contain letters, numbers, and underscores")
        
        return value.lower()
    
    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value.lower()
    
    def validate_phone(self, value):
        if value and not re.match(r'^\+?[1-9]\d{1,14}$', value):
            raise serializers.ValidationError("Invalid phone number format")
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        
        if not attrs.get('username') and not attrs.get('email'):
            raise serializers.ValidationError("Either username or email must be provided")
        
        # Validate organization code if provided
        org_code = attrs.get('organization_code')
        if org_code:
            try:
                organization = Organization.objects.get(code=org_code.upper())
                attrs['organization'] = organization
            except Organization.DoesNotExist:
                raise serializers.ValidationError("Invalid organization code")
        
        return attrs
    
    def create(self, validated_data):
        # Remove confirmation fields
        validated_data.pop('password_confirm', None)
        validated_data.pop('organization_code', None)
        
        # Set default role based on organization type
        organization = validated_data.get('organization')
        if organization:
            if organization.type == 'vendor':
                validated_data['role'] = 'vendor_admin'
            else:
                validated_data['role'] = 'operator'
        else:
            validated_data['role'] = 'viewer'
        
        # Create user
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        return user

class FlexibleLoginSerializer(serializers.Serializer):
    """
    Serializer for login that accepts either username or email
    """
    login = serializers.CharField(
        help_text="Enter your username or email address"
    )
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        login = attrs.get('login')
        password = attrs.get('password')
        
        if login and password:
            # Use custom authentication backend
            user = authenticate(
                request=self.context.get('request'),
                username=login,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    "Unable to log in with provided credentials."
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    "User account is disabled."
                )
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                "Must include login and password."
            )

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT serializer that supports email/username login
    """
    
    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        if not username or not password:
            raise serializers.ValidationError("Username and password are required.")

        try:
            user = User.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials.")

        user = authenticate(username=user.username, password=password)
        if user is None or not user.is_active:
            raise serializers.ValidationError("Invalid credentials or inactive account.")

        self.user = user
        
        data = super().validate(attrs)
        
        # Add user info to response
        user = self.user
        data['user'] = {
            'id': str(user.id),
            'username': user.username,
            'email': user.email,
            'full_name': f"{user.first_name} {user.last_name}".strip(),
            'role': user.role,
            'organization': {
                'id': str(user.organization.id) if user.organization else None,
                'name': user.organization.name if user.organization else None,
                'code': user.organization.code if user.organization else None,
                'type': user.organization.type if user.organization else None,
            } if user.organization else None,
            'is_active': user.is_active,
            'last_login': user.last_login,
            'email_verified': user.email_verified
        }
        
        return data

class GoogleAuthSerializer(serializers.Serializer):
    google_token = serializers.CharField(required=True)
    organization_code = serializers.CharField(required=False, allow_blank=True)
    
    def validate_organization_code(self, value):
        if value:
            try:
                return Organization.objects.get(code=value.upper())
            except Organization.DoesNotExist:
                raise serializers.ValidationError("Invalid organization code")
        return None

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email__iexact=value, is_active=True)
            return value.lower()
        except User.DoesNotExist:
            raise serializers.ValidationError("No active user found with this email")

class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords do not match")
        return attrs

class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField(required=True)

class ResendEmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email__iexact=value)
            if user.email_verified:
                raise serializers.ValidationError("Email is already verified")
            return value.lower()
        except User.DoesNotExist:
            raise serializers.ValidationError("No user found with this email")