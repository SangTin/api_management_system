from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import CommandRequest, CommandExecution
from .serializers import CommandRequestSerializer, CommandExecutionSerializer
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from shared.kafka.publisher import EventPublisher
from shared.kafka.topics import Topics, EventTypes
import uuid
from shared.permissions import (
    IsAdminUser,
    IsViewer, 
    IsOwnerOrAdmin,
    require_role,
    organization_required,
    BaseMixin,
    OrganizationFilterMixin,
    PermissionRequiredMixin,
)

class CommandRequestViewSet(PermissionRequiredMixin, OrganizationFilterMixin, viewsets.ModelViewSet):
    """ViewSet for command requests"""
    queryset = CommandRequest.objects.all()
    serializer_class = CommandRequestSerializer
    
    @action(detail=False, methods=['post'], url_path='execute')
    def execute_command(self, request):
        """Execute a command on a device"""
        device_id = request.data.get('device_id')
        command_type = request.data.get('command_type')
        params = request.data.get('params', {})
        
        if not device_id or not command_type:
            return Response(
                {'error': 'device_id and command_type are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        # Create command request
        command_id = str(uuid.uuid4())
        command_request = CommandRequest.objects.create(
            id=command_id,
            device_id=device_id,
            command_type=command_type,
            command_params=params,
            user_id=str(request.user.id),
            status='queued'
        )
        
        # Publish command request event
        EventPublisher.publish_event(
            Topics.DEVICE_COMMANDS,
            EventTypes.DEVICE_COMMAND_REQUESTED,
            {
                'command_id': command_id,
                'device_id': device_id,
                'command_type': command_type,
                'command_params': params,
                'user_id': str(request.user.id)
            }
        )
        
        return Response({
            'success': True,
            'command_id': command_id,
            'message': 'Command execution initiated'
        })
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """Get command execution status"""
        try:
            command = self.get_object()
            
            # Get the latest execution if available
            execution = CommandExecution.objects.filter(
                command_request_id=command.id
            ).order_by('-completed_at').first()
            
            result = {
                'command_id': str(command.id),
                'status': command.status,
                'device_id': command.device_id,
                'command_type': command.command_type,
                'created_at': command.created_at,
                'updated_at': command.updated_at,
            }
            
            if execution:
                result['execution'] = {
                    'execution_id': str(execution.id),
                    'agent_id': execution.agent_id,
                    'started_at': execution.started_at,
                    'completed_at': execution.completed_at,
                    'execution_time': execution.execution_time,
                    'result': execution.result
                }
            
            return Response(result)
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )