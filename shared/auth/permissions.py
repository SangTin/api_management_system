from rest_framework.permissions import BasePermission

class HasRole(BasePermission):
    """
    Permission class để check user role
    
    Usage:
        @permission_classes([HasRole])
        class MyViewSet(ViewSet):
            required_roles = ['admin', 'operator']
    """
    
    def has_permission(self, request, view):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
        
        required_roles = getattr(view, 'required_roles', [])
        if not required_roles:
            return True
        
        return hasattr(request.user, 'role') and request.user.role in required_roles

class SameOrganization(BasePermission):
    """
    Permission class để check user thuộc cùng organization
    """
    
    def has_permission(self, request, view):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
        
        # Admin có thể access tất cả
        if hasattr(request.user, 'role') and request.user.role == 'admin':
            return True
        
        return hasattr(request.user, 'organization_id') and request.user.organization_id

    def has_object_permission(self, request, view, obj):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
            
        # Admin có thể access tất cả objects
        if hasattr(request.user, 'role') and request.user.role == 'admin':
            return True
        
        # Kiểm tra object có thuộc cùng organization không
        if hasattr(obj, 'organization_id'):
            return str(obj.organization_id) == str(getattr(request.user, 'organization_id', ''))
        
        # Kiểm tra object được tạo bởi user hiện tại
        if hasattr(obj, 'created_by'):
            return str(obj.created_by) == str(getattr(request.user, 'user_id', ''))
        
        return False

class IsOwnerOrAdmin(BasePermission):
    """
    Permission class để check user là owner hoặc admin
    """
    
    def has_object_permission(self, request, view, obj):
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return False
            
        # Admin có quyền access tất cả
        if hasattr(request.user, 'role') and request.user.role == 'admin':
            return True
        
        # Check nếu user là owner
        if hasattr(obj, 'created_by'):
            return str(obj.created_by) == str(getattr(request.user, 'user_id', ''))
        
        if hasattr(obj, 'owner_id'):
            return str(obj.owner_id) == str(getattr(request.user, 'user_id', ''))
        
        return False