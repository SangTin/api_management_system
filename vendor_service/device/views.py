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
            
            if current_primary:
                current_primary.is_primary = False
                current_primary.save()
            
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
            
    @action(detail=True, methods=['post'], url_path='run')
    def run_command(self, request, pk=None):
        """
        Execute command on device
        POST /api/device-commands/{id}/run/
        
        Body:
        {
            "params": {
                "param1": "value1",
                "param2": "value2"
            }
        }
        """
        try:
            device_command = self.get_object()
            
            # Validate device command is active and has command template
            if not device_command.is_active:
                return Response(
                    {'error': 'Device command is not active'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not device_command.command:
                return Response(
                    {'error': 'No command template associated with this device command'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get command parameters
            command_params = request.data.get('params', {})
            
            # Validate required parameters
            required_params = device_command.command.required_params or []
            missing_params = [param for param in required_params if param not in command_params]
            
            if missing_params:
                return Response(
                    {'error': f'Missing required parameters: {", ".join(missing_params)}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Generate unique command ID
            command_id = str(uuid.uuid4())
            
            # Prepare command data for Kafka
            command_data = {
                'command_id': command_id,
                'device_id': str(device_command.device.id),
                'command_type': device_command.command_type,
                'command_params': command_params,
                'user_id': str(request.user.id) if request.user.is_authenticated else 'anonymous',
                'timestamp': timezone.now().isoformat(),
                'device_command_id': str(device_command.id),
                'command_template_id': str(device_command.command.id)
            }
            
            # Publish command to Kafka for execution
            EventPublisher.publish_command_event(
                EventTypes.DEVICE_COMMAND_REQUESTED,
                command_data
            )
            
            # Return immediate response with command ID for tracking
            return Response({
                'success': True,
                'command_id': command_id,
                'message': 'Command sent for execution',
                'device': {
                    'id': str(device_command.device.id),
                    'name': device_command.device.name
                },
                'command_type': device_command.command_type,
                'status': 'queued'
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to execute command: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )