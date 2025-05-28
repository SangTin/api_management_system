from functools import wraps
from django.http import JsonResponse

def require_role(*allowed_roles):
    """
    Decorator để yêu cầu user có một trong các roles được chỉ định
    
    Usage:
        @require_role('admin', 'operator')
        def my_view(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user_role = getattr(request, 'user_role', None)
            
            if not user_role:
                return JsonResponse({
                    'error': 'Authentication required',
                    'message': 'User role not found in request'
                }, status=401)
            
            if user_role not in allowed_roles:
                return JsonResponse({
                    'error': 'Permission denied',
                    'message': f'Required roles: {", ".join(allowed_roles)}. Your role: {user_role}'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def require_organization(allow_admin=True):
    """
    Decorator để yêu cầu user thuộc về một organization
    
    Usage:
        @require_organization()
        def my_view(request):
            pass
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            organization_id = getattr(request, 'organization_id', None)
            user_role = getattr(request, 'user_role', None)
            
            # Admin có thể bypass nếu allow_admin=True
            if allow_admin and user_role == 'admin':
                return view_func(request, *args, **kwargs)
            
            if not organization_id:
                return JsonResponse({
                    'error': 'Organization required',
                    'message': 'User must belong to an organization'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def require_emergency_override():
    """
    Decorator cho các operations cần emergency override
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            emergency_override = getattr(request, 'emergency_override', False)
            user_role = getattr(request, 'user_role', None)
            
            if not emergency_override and user_role != 'admin':
                return JsonResponse({
                    'error': 'Emergency override required',
                    'message': 'This operation requires emergency override authorization'
                }, status=403)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator