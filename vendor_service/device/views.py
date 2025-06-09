from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Device, DeviceCommand
from .serializers import DeviceSerializer, DeviceCommandSerializer

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
    
class DeviceCommandViewSet(PermissionRequiredMixin, OrganizationFilterMixin, viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['command']
    search_fields = ['device__name', 'command__name', 'command__id']
    ordering_fields = ['device__name', 'command__name', 'created_at']
    queryset = DeviceCommand.objects.all()
    serializer_class = DeviceCommandSerializer

    permission_map = {
        'list': [IsAdminUser],
        'retrieve': [IsOwnerOrAdmin],
        'create': [IsAdminUser],
        'update': [IsOwnerOrAdmin],
        'partial_update': [IsOwnerOrAdmin],
        'destroy': [IsAdminUser],
    }
    
    def list(self, request, *args, **kwargs):
        commands = self.filter_queryset(self.get_queryset())
        data = {}

        for command in commands:
            command_type = command.command_type
            if command_type not in data:
                data[command_type] = []
            data[command_type].append(DeviceCommandSerializer(command).data)

        return Response(data, status=status.HTTP_200_OK)