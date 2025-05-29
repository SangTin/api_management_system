from django.urls import path
from .views import (
    UserRegistrationView, CustomTokenObtainPairView, google_auth,
    password_reset_request, password_reset_confirm, email_verify,
    logout, verify_token, verify_api_key, resend_email_verification,
    user_profile
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    # Registration & Login
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('logout/', logout, name='logout'),
    
    # Google OAuth
    path('google/', google_auth, name='google-auth'),
    
    # Token management
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('verify-token/', verify_token, name='verify-token'),
    path('verify-api-key/', verify_api_key, name='verify-api-key'),
    
    # Password reset
    path('password-reset/', password_reset_request, name='password-reset'),
    path('password-reset/confirm/', password_reset_confirm, name='password-reset-confirm'),
    
    # Email verification
    path('email-verify/', email_verify, name='email-verify'),
    path('resend-verification/', resend_email_verification, name='resend-email-verification'),
    
    # User management
    path('profile/', user_profile, name='user-profile'),
]