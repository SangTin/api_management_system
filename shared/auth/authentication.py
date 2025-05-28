from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
import logging

logger = logging.getLogger(__name__)

class KongUser:
    """
    Authenticated user object từ Kong headers
    """
    def __init__(self, user_id, username, role, organization_id=None, **kwargs):
        self.id = user_id
        self.user_id = user_id
        self.username = username
        self.role = role
        self.organization_id = organization_id
        self.clearance_level = kwargs.get('clearance_level', 1)
        self.emergency_override = kwargs.get('emergency_override', False)
        self.is_authenticated = True
        self.is_active = True

    def __str__(self):
        return f"{self.username} ({self.role})"

class AnonymousKongUser:
    """
    Anonymous user từ Kong (no auth token provided hoặc invalid token)
    """
    def __init__(self):
        self.id = None
        self.user_id = None
        self.username = "anonymous"
        self.role = "anonymous"
        self.organization_id = None
        self.clearance_level = 1
        self.emergency_override = False
        self.is_authenticated = False
        self.is_active = False

    def __str__(self):
        return "Anonymous"

class KongAuthentication(BaseAuthentication):
    """
    Kong Authentication - Always returns a user (authenticated or anonymous)
    
    Kong plugin behavior:
    1. No Authorization header → X-Authenticated: false → AnonymousKongUser
    2. Invalid token → X-Authenticated: false → AnonymousKongUser  
    3. Valid token → X-Authenticated: true + user info → KongUser
    
    Usage:
        # For protected endpoints
        @authentication_classes([KongAuthentication])
        @permission_classes([IsAuthenticated])
        def protected_view(request):
            # Only authenticated users reach here
            user = request.user  # KongUser object
        
        # For optional auth endpoints
        @authentication_classes([KongAuthentication])
        @permission_classes([AllowAny])
        def optional_auth_view(request):
            if request.user.is_authenticated:
                # Authenticated user
                message = f"Hello {request.user.username}"
            else:
                # Anonymous user
                message = "Hello anonymous"
    """

    def authenticate(self, request):
        """
        Extract user information từ Kong headers
        Always returns (user, token) - never None
        """
        # Check Kong authentication status
        authenticated = request.headers.get('X-Authenticated', '').lower() == 'true'
        
        if not authenticated:
            # Anonymous user (no token hoặc invalid token)
            logger.debug("Kong returned anonymous user")
            return (AnonymousKongUser(), None)
        
        # Authenticated user - extract info từ Kong headers
        user_id = request.headers.get('X-User-ID')
        username = request.headers.get('X-Username')
        user_role = request.headers.get('X-User-Role')
        organization_id = request.headers.get('X-Organization-ID')
        clearance_level = request.headers.get('X-Clearance-Level', '1')
        emergency_override = request.headers.get('X-Emergency-Override', '').lower() == 'true'
        
        print(f"X-User-ID: {user_id}, X-Username: {username}, X-User-Role: {user_role}, "
              f"X-Organization-ID: {organization_id}, X-Clearance-Level: {clearance_level}, "
              f"X-Emergency-Override: {emergency_override}")
        # Validate required fields
        if not user_id or not username:
            logger.warning("Kong authenticated but missing user info")
            return (AnonymousKongUser(), None)
        
        try:
            clearance_level = int(clearance_level)
        except (ValueError, TypeError):
            clearance_level = 1
        
        # Create authenticated user object
        user = KongUser(
            user_id=user_id,
            username=username,
            role=user_role or 'user',
            organization_id=organization_id,
            clearance_level=clearance_level,
            emergency_override=emergency_override
        )
        
        logger.debug(f"Kong authenticated user: {user}")
        return (user, None)

    def authenticate_header(self, request):
        """
        Return authentication header cho WWW-Authenticate header
        """
        return 'Kong'