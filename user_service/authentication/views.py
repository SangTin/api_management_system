from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
import secrets
import string
from urllib.parse import urljoin

from .serializers import (
    UserRegistrationSerializer, CustomTokenObtainPairSerializer,
    FlexibleLoginSerializer, GoogleAuthSerializer, PasswordResetSerializer, 
    PasswordResetConfirmSerializer, EmailVerificationSerializer,
    ResendEmailVerificationSerializer
)

User = get_user_model()

class UserRegistrationView(generics.CreateAPIView):
    """User registration endpoint"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        
        # Print reason for validation failure if any
        if not serializer.is_valid():
            print("Validation errors:", serializer.errors)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Send email verification (optional)
        if getattr(settings, 'EMAIL_VERIFICATION_ENABLED', False):
            self.send_verification_email(user, request)
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'User registered successfully',
            'email_verification_sent': getattr(settings, 'EMAIL_VERIFICATION_ENABLED', False),
            'user': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'email_verified': user.email_verified
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }
        }, status=status.HTTP_201_CREATED)
    
    def send_verification_email(self, user, request):
        """Send email verification"""
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        base_url = (settings.FRONTEND_URL or request.build_absolute_uri('/')).rstrip('/')
        relative_path = 'email-verify'
        verification_url = f"{base_url}/{relative_path}?token={token}&uid={uid}"

        send_mail(
            'Verify your email address',
            f'Please click the link to verify your email: {verification_url}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

class FlexibleLoginView(generics.GenericAPIView):
    """Login with username or email"""
    serializer_class = FlexibleLoginSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Update last login
        from django.utils import timezone
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Login successful',
            'user': {
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
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })

class CustomTokenObtainPairView(TokenObtainPairView):
    """JWT login with username or email"""
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Update last login
            login = request.data.get('login')
            try:
                from django.db.models import Q
                user = User.objects.get(
                    Q(username__iexact=login) | Q(email__iexact=login)
                )
                from django.utils import timezone
                user.last_login = timezone.now()
                user.save(update_fields=['last_login'])
            except User.DoesNotExist:
                pass
        
        return response

@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
    """Google OAuth authentication"""
    serializer = GoogleAuthSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    google_token = serializer.validated_data['google_token']
    organization = serializer.validated_data.get('organization_code')
    
    try:
        # Verify Google token
        try:
            idinfo = id_token.verify_oauth2_token(
                google_token, 
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID,
                clock_skew_in_seconds=10
            )
        except ValueError as e:
            print(f"Google token verification failed: {str(e)}")
            return Response({'error': f'Invalid Google token: {str(e)}'}, status=400)

        # Extract user info from Google
        email = idinfo.get('email')
        first_name = idinfo.get('given_name', '')
        last_name = idinfo.get('family_name', '')
        google_id = idinfo.get('sub')
        email_verified = idinfo.get('email_verified', False)
        
        if not email:
            return Response(
                {'error': 'Email not provided by Google'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user exists
        try:
            user = User.objects.get(email__iexact=email)
            # Update Google ID and email verification if not set
            updated_fields = []
            if not user.google_id:
                user.google_id = google_id
                updated_fields.append('google_id')
            if not user.email_verified and email_verified:
                user.email_verified = True
                updated_fields.append('email_verified')
            if updated_fields:
                user.save(update_fields=updated_fields)
        except User.DoesNotExist:
            user = User.objects.create_user(
                email=email,
                first_name=first_name,
                last_name=last_name,
                google_id=google_id,
                organization=organization,
                role='viewer' if not organization else (
                    'vendor_admin' if organization.type == 'vendor' else 'operator'
                ),
                is_active=True,
                email_verified=email_verified
            )
        
        # Update last login
        from django.utils import timezone
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'message': 'Google authentication successful',
            'user': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'full_name': f"{user.first_name} {user.last_name}".strip(),
                'role': user.role,
                'organization': {
                    'id': str(user.organization.id) if user.organization else None,
                    'name': user.organization.name if user.organization else None,
                    'code': user.organization.code if user.organization else None,
                } if user.organization else None,
                'email_verified': user.email_verified
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        })
        
    except ValueError as e:
        return Response(
            {'error': 'Invalid Google token'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )
    except Exception as e:
        return Response(
            {'error': 'Google authentication failed'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([AllowAny])
def resend_email_verification(request):
    """Resend email verification"""
    serializer = ResendEmailVerificationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    user = User.objects.get(email__iexact=email)
    
    # Generate verification token
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Send verification email
    base_url = (settings.FRONTEND_URL or request.build_absolute_uri('/')).rstrip('/')
    relative_path = 'email-verify'
    verification_url = f"{base_url}/{relative_path}?token={token}&uid={uid}"
    
    send_mail(
        'Verify your email address',
        f'Please click the link to verify your email: {verification_url}',
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
    
    return Response({
        'message': 'Verification email sent successfully'
    })
    
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """Request password reset"""
    serializer = PasswordResetSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    user = User.objects.get(email=email)
    
    # Generate reset token
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Send reset email
    reset_url = request.build_absolute_uri(
        reverse('password-reset-confirm') + f'?token={token}&uid={uid}'
    )
    
    send_mail(
        'Password Reset Request',
        f'Click the link to reset your password: {reset_url}',
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
    
    return Response({
        'message': 'Password reset email sent successfully'
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request):
    """Confirm password reset"""
    serializer = PasswordResetConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    token = serializer.validated_data['token']
    new_password = serializer.validated_data['new_password']
    
    # Extract uid from query params or request data
    uid = request.query_params.get('uid') or request.data.get('uid')
    if not uid:
        return Response(
            {'error': 'UID is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
        
        if default_token_generator.check_token(user, token):
            user.set_password(new_password)
            user.save()
            
            return Response({
                'message': 'Password reset successfully'
            })
        else:
            return Response(
                {'error': 'Invalid or expired token'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response(
            {'error': 'Invalid reset link'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
@permission_classes([AllowAny])
def email_verify(request):
    """Email verification endpoint"""
    token = request.query_params.get('token')
    uid = request.query_params.get('uid')
    
    if not token or not uid:
        return Response(
            {'error': 'Token and UID are required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        user_id = force_str(urlsafe_base64_decode(uid))
        user = User.objects.get(pk=user_id)
        
        if default_token_generator.check_token(user, token):
            user.email_verified = True
            user.save()
            
            return Response({
                'message': 'Email verified successfully'
            })
        else:
            return Response(
                {'error': 'Invalid or expired verification link'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return Response(
            {'error': 'Invalid verification link'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Logout user by blacklisting refresh token"""
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({
            'message': 'Logged out successfully'
        })
    except Exception as e:
        return Response(
            {'error': 'Invalid token'}, 
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_token(request):
    """Endpoint for other services to verify JWT tokens"""
    return Response({
        'valid': True,
        'user_id': str(request.user.id),
        'username': request.user.username,
        'role': request.user.role,
        'organization_id': str(request.user.organization.id) if request.user.organization else None
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def verify_api_key(request):
    """Endpoint for API key verification"""
    api_key = request.data.get('api_key')
    try:
        user = User.objects.get(api_key=api_key, is_api_user=True)
        return Response({
            'valid': True,
            'user_id': str(user.id),
            'role': user.role,
            'organization_id': str(user.organization.id) if user.organization else None
        })
    except User.DoesNotExist:
        return Response({'valid': False}, status=401)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """Get user profile information"""
    user = request.user
    return Response({
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
        'email_verified': user.email_verified
    })