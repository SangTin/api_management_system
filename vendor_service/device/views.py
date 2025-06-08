from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Device
from .serializers import DeviceSerializer

from shared.permissions import (
    IsAdminUser,
    IsViewer, 
    IsOwnerOrAdmin,
    require_role,
    organization_required,
    PermissionRequiredMixin,
    OrganizationFilterMixin
)

class DeviceViewSet(PermissionRequiredMixin, OrganizationFilterMixin, viewsets.ModelViewSet):
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'created_at']
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer

    permission_map = {
        'list': [IsAdminUser],
        'retrieve': [IsOwnerOrAdmin],
        'create': [IsAdminUser],
        'update': [IsOwnerOrAdmin],
        'partial_update': [IsOwnerOrAdmin],
        'destroy': [IsAdminUser],
        'activate': [IsAdminUser],
        'deactivate': [IsAdminUser],
    }