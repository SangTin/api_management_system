from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
import jwt

from user.models import User

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            # Add user info to response
            user = User.objects.get(username=request.data['username'])
            response.data['user'] = {
                'id': str(user.id),
                'username': user.username,
                'role': user.role,
                'organization_id': str(user.organization.id) if user.organization else None
            }
        return response

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
@permission_classes([AllowAny])
@authentication_classes([])
def public_endpoint(request):
    """Public endpoint for testing purposes"""
    return Response({'message': 'This is a public endpoint, accessible without authentication.'})