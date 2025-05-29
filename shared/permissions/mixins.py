from django.core.exceptions import PermissionDenied
from django.db.models import QuerySet
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from shared.permissions.base import IsViewer, IsOperator, IsAdminUser, IsVendorAdmin, IsOwnerOrAdmin

class OrganizationFilterMixin:
    """Mixin để filter data theo organization của user"""
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return self.filter_queryset_by_organization(queryset)
    
    def filter_queryset_by_organization(self, queryset: QuerySet) -> QuerySet: 
        """Filter queryset theo organization của user"""
        user = self.request.user
        
        if not user or not user.is_authenticated:
            return queryset.none()
        
        # Admin thấy tất cả
        if user.role == 'admin':
            return queryset
        
        # Vendor admin chỉ thấy data của vendor mình
        if user.role == 'vendor_admin':
            if hasattr(queryset.model, 'vendor'):
                return queryset.filter(vendor__organization=user.organization)
            elif hasattr(queryset.model, 'organization'):
                return queryset.filter(organization=user.organization)
        
        # Các role khác chỉ thấy data của organization mình
        if hasattr(queryset.model, 'organization'):
            return queryset.filter(organization=user.organization)
        
        # Fallback: chỉ thấy data của chính mình
        if hasattr(queryset.model, 'user'):
            return queryset.filter(user=user)
        
        return queryset
    
class PermissionRequiredMixin:
    """Mixin để check permission theo action"""
    permission_map = {
        'list': [IsViewer],
        'retrieve': [IsViewer], 
        'create': [IsOperator],
        'update': [IsOperator],
        'partial_update': [IsOperator],
        'destroy': [IsAdminUser],
    }
    
    def get_permissions(self):
        """Override để set permission theo action"""
        action = getattr(self, 'action', None)
        
        if action and action in self.permission_map:
            permission_classes = self.permission_map[action]
        else:
            permission_classes = getattr(self, 'permission_classes', [])
        
        return [permission() for permission in permission_classes]
    
    