from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import APIConfiguration, CommandTemplate
from .serializers import APIConfigurationSerializer, CommandTemplateSerializer
from shared.models.constants import HTTP_METHOD_CHOICES, AUTH_CHOICES
from shared.kafka.publisher import EventPublisher, EventTypes
from shared.kafka.topics import Topics
import time
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

class APIConfigurationViewSet(PermissionRequiredMixin, OrganizationFilterMixin, viewsets.ModelViewSet):
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'id']
    ordering_fields = ['name', 'created_at']
    queryset = APIConfiguration.objects.all()
    serializer_class = APIConfigurationSerializer
    
    permission_map = {
        'list': [IsOwnerOrAdmin],
        'retrieve': [IsOwnerOrAdmin],
        'create': [IsAdminUser],
        'update': [IsOwnerOrAdmin],
        'partial_update': [IsOwnerOrAdmin],
        'destroy': [IsAdminUser],
    }
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        api_config = serializer.save()
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        api_config = serializer.save()
        
        return Response(serializer.data)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        vendor_id = request.query_params.get('vendor_id')
        if vendor_id:
            queryset = queryset.filter(vendor_id=vendor_id)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='test-command')
    def test_command(self, request, pk=None):
        api_config = self.get_object()
        command_id = request.data.get('command_id')
        params = request.data.get('params', {})
        
        test_id = str(uuid.uuid4())
        
        # Publish to API test topic
        EventPublisher.publish_event(
            Topics.API_TEST_REQUESTS,
            EventTypes.API_TEST_REQUESTED,
            {
                'test_id': test_id,
                'api_config_id': str(api_config.id),
                'command_id': command_id,
                'params': params,
                'user_id': str(request.user.id),
            }
        )
        
        return Response({
            'success': True,
            'test_id': test_id,
            'message': 'API test initiated successfully.'
        })
    
    @action(detail=False, methods=['get'], url_path='auth-methods')
    def auth_methods(self, request, pk=None):
        """
        Returns the list of supported authentication methods.
        """
        auth_methods = ({"value": code, "label": label} for code, label in AUTH_CHOICES)
        return Response(auth_methods, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='commands')
    def commands(self, request, pk=None):
        api_configs = self.filter_queryset(self.get_queryset())
        commands = []
        
        # Add commands for each API config
        for api_config in api_configs:
            api_commands = CommandTemplate.objects.filter(api_config=api_config)
            if api_commands.exists():
                commands.append({
                    'id': str(api_config.id),
                    'name': api_config.name,
                    'version': api_config.version,
                    'type': 'api_config',
                    'commands': [
                        {
                            'id': str(cmd.id),
                            'command_type': cmd.command_type,
                            'name': cmd.name,
                            'method': cmd.method,
                        } for cmd in api_commands
                    ]
                })
        
        # Add commands without API config to "Others" group
        orphan_commands = CommandTemplate.objects.filter(api_config__isnull=True)
        if orphan_commands.exists():
            commands.append({
                'id': 'others',
                'name': 'Others',
                'type': 'others',
                'commands': [
                    {
                        'id': str(cmd.id),
                        'command_type': cmd.command_type,
                        'name': cmd.name,
                        'method': cmd.method,
                    } for cmd in orphan_commands
                ]
            })
        
        return Response(commands, status=status.HTTP_200_OK)

class CommandTemplateViewSet(PermissionRequiredMixin, OrganizationFilterMixin, viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['command_type', 'api_config']
    search_fields = ['name', 'id', 'command_type']
    ordering_fields = ['name', 'created_at', 'command_type']
    queryset = CommandTemplate.objects.all()
    serializer_class = CommandTemplateSerializer

    permission_map = {
        'list': [IsOwnerOrAdmin],
        'retrieve': [IsOwnerOrAdmin],
        'create': [IsAdminUser],
        'update': [IsOwnerOrAdmin],
        'partial_update': [IsOwnerOrAdmin],
        'destroy': [IsAdminUser],
    }
    
    def create(self, request, *args, **kwargs):
        """Create command template và publish event"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        command_template = serializer.save()
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='methods')
    def methods(self, request, pk=None):
        """
        Returns the list of supported HTTP methods.
        """
        methods = ({"value": code, "label": label} for code, label in HTTP_METHOD_CHOICES)
        return Response(methods, status=status.HTTP_200_OK)