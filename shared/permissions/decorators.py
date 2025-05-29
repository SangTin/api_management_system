from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import PermissionDenied

def require_role(*allowed_roles):
    """Decorator để yêu cầu specific roles"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user or not request.user.is_authenticated:
                return Response(
                    {'error': 'Authentication required'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            if request.user.role not in allowed_roles:
                return Response(
                    {'error': f'Required roles: {", ".join(allowed_roles)}'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def require_permission(permission_check_func):
    """Decorator với custom permission check function"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not permission_check_func(request.user):
                return Response(
                    {'error': 'Permission denied'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def organization_required(view_func):
    """Decorator yêu cầu user phải thuộc organization"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if (not request.user or 
            not request.user.is_authenticated or 
            not request.user.organization):
            return Response(
                {'error': 'Organization membership required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return view_func(request, *args, **kwargs)
    return wrapper
