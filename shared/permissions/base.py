from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied
from typing import List, Optional

class BaseMicroservicePermission(BasePermission):
    """Base permission class cho microservices"""
    required_roles: List[str] = []
    message: str = "Bạn không có quyền truy cập chức năng này."
    
    def has_permission(self, request, view):
        user_id = request.headers.get('X-User-ID')
        user_role = request.headers.get('X-User-Role')
        
        if not user_id or not user_role:
            return False
            
        return user_role in self.required_roles
    
    def get_user_info(self, request):
        """Extract user info từ headers"""
        return {
            'id': request.headers.get('X-User-ID'),
            'role': request.headers.get('X-User-Role'),
            'organization_id': request.headers.get('X-Organization-ID'),
            'username': request.headers.get('X-Username'),
        }

class IsAdminUser(BaseMicroservicePermission):
    """Chỉ Admin mới có quyền"""
    required_roles = ['admin']
    message = "Chỉ Admin mới có quyền thực hiện hành động này."

class IsVendorAdmin(BaseMicroservicePermission):
    """Vendor Admin và Admin có quyền"""
    required_roles = ['admin', 'vendor_admin']

class IsOperator(BaseMicroservicePermission):
    """Operator, Vendor Admin và Admin có quyền"""
    required_roles = ['admin', 'operator', 'vendor_admin']

class IsViewer(BaseMicroservicePermission):
    """Tất cả authenticated users có quyền xem"""
    required_roles = ['admin', 'operator', 'viewer', 'vendor_admin']

class IsOwnerOrAdmin(BaseMicroservicePermission):
    """Owner của organization hoặc admin có quyền"""
    message = "Bạn chỉ có thể truy cập dữ liệu của tổ chức mình."
    
    def has_permission(self, request, view):
        user_info = self.get_user_info(request)
        return user_info['id'] is not None
    
    def has_object_permission(self, request, view, obj):
        user_info = self.get_user_info(request)
        
        # Admin có quyền truy cập tất cả
        if user_info['role'] == 'admin':
            return True
        
        # Kiểm tra ownership dựa trên organization_id
        if hasattr(obj, 'organization_id'):
            return str(obj.organization_id) == user_info['organization_id']
        
        # Kiểm tra ownership trực tiếp với user_id
        if hasattr(obj, 'user_id'):
            return str(obj.user_id) == user_info['id']
            
        return False