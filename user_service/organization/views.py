from rest_framework import viewsets
from shared.permissions import IsAdminUser, IsVendorAdmin, OrganizationFilterMixin, PermissionRequiredMixin
from .models import Organization
from .serializers import OrganizationSerializer

class OrganizationViewSet(PermissionRequiredMixin, OrganizationFilterMixin, viewsets.ModelViewSet):
    """ViewSet cho Organization management"""
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    
    permission_map = {
        'list': [IsVendorAdmin],
        'retrieve': [IsVendorAdmin],
        'create': [IsAdminUser],
        'update': [IsAdminUser],
        'partial_update': [IsAdminUser],
        'destroy': [IsAdminUser],
    }