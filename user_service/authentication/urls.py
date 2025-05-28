from django.urls import path
from .views import CustomTokenObtainPairView, verify_token, verify_api_key, public_endpoint
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.views import TokenBlacklistView

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/blacklist/', TokenBlacklistView.as_view(), name='token_blacklist'),
    path('verify-token/', verify_token, name='verify_token'),
    path('verify-api-key/', verify_api_key, name='verify_api_key'),
    path('public-endpoint/', public_endpoint, name='public_endpoint'),
]
