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
    PermissionRequiredMixin,
    OrganizationFilterMixin
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
            
class CommandExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for command execution tracking
    """
    queryset = CommandRequest.objects.all()
    serializer_class = CommandRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'device_id', 'command_type']
    search_fields = ['device_id', 'command_type', 'user_id']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    @action(detail=True, methods=['get'], url_path='status')
    def get_status(self, request, pk=None):
        """
        Get detailed execution status for a command
        GET /api/command-executions/{command_id}/status/
        """
        try:
            command_request = self.get_object()
            
            response_data = {
                'command_id': str(command_request.id),
                'status': command_request.status,
                'device_id': command_request.device_id,
                'command_type': command_request.command_type,
                'command_params': command_request.command_params,
                'user_id': command_request.user_id,
                'retry_count': command_request.retry_count,
                'max_retries': command_request.max_retries,
                'created_at': command_request.created_at.isoformat(),
                'updated_at': command_request.updated_at.isoformat(),
            }
            
            # Add execution details if available
            try:
                execution = CommandExecution.objects.get(command_request=command_request)
                response_data.update({
                    'execution': {
                        'agent_id': execution.agent_id,
                        'api_config_id': execution.api_config_id,
                        'protocol': execution.protocol,
                        'result': execution.result,
                        'error_message': execution.error_message,
                        'response_data': execution.response_data,
                        'execution_time': execution.execution_time,
                        'response_size': execution.response_size,
                        'started_at': execution.started_at.isoformat(),
                        'completed_at': execution.completed_at.isoformat(),
                    }
                })
            except CommandExecution.DoesNotExist:
                response_data['execution'] = None
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get execution status: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='by-command-id/(?P<command_id>[^/.]+)')
    def get_by_command_id(self, request, command_id=None):
        """
        Get execution status by command ID (UUID)
        GET /api/command-executions/by-command-id/{command_id}/
        """
        try:
            command_request = get_object_or_404(CommandRequest, id=command_id)
            return self.get_status(request, pk=command_request.id)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get execution status: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='device/(?P<device_id>[^/.]+)')
    def get_by_device(self, request, device_id=None):
        """
        Get all command executions for a device
        GET /api/command-executions/device/{device_id}/
        """
        try:
            queryset = self.filter_queryset(
                self.get_queryset().filter(device_id=device_id)
            )
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get device executions: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='stats')
    def get_stats(self, request):
        """
        Get execution statistics
        GET /api/command-executions/stats/
        """
        try:
            from django.db.models import Count, Avg
            from datetime import datetime, timedelta
            
            # Get query parameters
            days = int(request.query_params.get('days', 7))
            device_id = request.query_params.get('device_id')
            
            # Filter by date range
            start_date = datetime.now() - timedelta(days=days)
            queryset = self.get_queryset().filter(created_at__gte=start_date)
            
            # Filter by device if specified
            if device_id:
                queryset = queryset.filter(device_id=device_id)
            
            # Calculate stats
            total_commands = queryset.count()
            status_counts = queryset.values('status').annotate(count=Count('status'))
            
            # Execution stats (only for completed commands)
            execution_queryset = CommandExecution.objects.filter(
                command_request__in=queryset,
                command_request__status='completed'
            )
            
            avg_execution_time = execution_queryset.aggregate(
                avg_time=Avg('execution_time')
            )['avg_time'] or 0
            
            # Command type stats
            command_type_stats = queryset.values('command_type').annotate(
                count=Count('command_type')
            ).order_by('-count')
            
            return Response({
                'period_days': days,
                'device_id': device_id,
                'total_commands': total_commands,
                'status_breakdown': {item['status']: item['count'] for item in status_counts},
                'average_execution_time': round(avg_execution_time, 2),
                'command_type_breakdown': list(command_type_stats),
                'generated_at': datetime.now().isoformat()
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to get execution stats: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )