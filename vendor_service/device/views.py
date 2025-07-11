from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Device, DeviceCommand
from .serializers import DeviceSerializer, DeviceCommandSerializer
import uuid
from django.utils import timezone
from shared.kafka.publisher import EventPublisher
from shared.kafka.topics import Topics, EventTypes

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
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
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
        device_id = request.query_params.get('device', None)
        if device_id:
            try:
                device = Device.objects.get(id=device_id)
                commands = commands.filter(device=device)
            except Device.DoesNotExist:
                return Response({'error': 'Device not found'}, status=status.HTTP_404_NOT_FOUND)
        data = {}

        for command in commands:
            command_type = command.command_type
            if command_type not in data:
                data[command_type] = []
            data[command_type].append(DeviceCommandSerializer(command).data)

        return Response(data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def toggle_primary(self, request, pk=None):
        """Toggle this command as the primary command for its type on the device"""
        device_command = self.get_object()
        device = device_command.device
        command_type = device_command.command_type
        
        if device_command.is_primary:
            # If already primary, remove primary status
            device_command.is_primary = False
            device_command.save()
            
            from shared.kafka.publisher import EventPublisher
            from shared.kafka.topics import Topics, EventTypes
            
            EventPublisher.publish_event(
                Topics.DEVICE_STATUS,
                EventTypes.DEVICE_COMMANDS_DISCONNECTED,
                {
                    'device_id': str(device.id),
                    'command_type': command_type,
                    'new_primary_command_id': None,
                    'previous_primary_command_id': str(device_command.id),
                    'user_id': str(request.user.id)
                }
            )
            
            return Response({
                'message': f'Command removed as primary for {command_type}',
                'device_command': DeviceCommandSerializer(device_command).data
            })
        else:
            # If not primary, make it primary
            current_primary = DeviceCommand.objects.filter(
                device=device,
                command_type=command_type,
                is_primary=True,
                is_active=True,
                is_deleted=False
            ).first()
            print(f"Current primary command: {current_primary}")
            
            if current_primary:
                current_primary.is_primary = False
                current_primary.save()
            
            print(f"Setting command {device_command.id} as primary for device {device.id} and command type {command_type}")
            
            device_command.is_primary = True
            device_command.save()
            
            from shared.kafka.publisher import EventPublisher
            from shared.kafka.topics import Topics, EventTypes
            
            EventPublisher.publish_event(
                Topics.DEVICE_STATUS,
                EventTypes.DEVICE_COMMANDS_DISCONNECTED,
                {
                    'device_id': str(device.id),
                    'command_type': command_type,
                    'new_primary_command_id': str(device_command.id),
                    'previous_primary_command_id': str(current_primary.id) if current_primary else None,
                    'user_id': str(request.user.id)
                }
            )
            
            return Response({
                'message': f'Command set as primary for {command_type}',
                'device_command': DeviceCommandSerializer(device_command).data
            })