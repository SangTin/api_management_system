from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import APIConfiguration, CommandTemplate
from .serializers import APIConfigurationSerializer, CommandTemplateSerializer
from .constants import HTTP_METHOD_CHOICES, AUTH_CHOICES
from protocol_handlers import get_protocol_handler
from shared.kafka.publisher import EventPublisher, EventTypes
import time

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
        
        # Publish API config created event
        EventPublisher.publish_api_config_event(
            EventTypes.API_CONFIG_CREATED,
            {
                'config_id': str(api_config.id),
                'name': api_config.name,
                'vendor_id': str(api_config.vendor.id),
                'vendor_name': api_config.vendor.name,
                'protocol': api_config.protocol,
                'version': api_config.version
            },
            str(request.user.id)
        )
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        old_data = {
            'name': instance.name,
            'version': instance.version,
            'protocol': instance.protocol,
            'base_url': instance.base_url,
            'is_active': instance.is_active
        }
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        api_config = serializer.save()
        
        # Publish API config updated event
        EventPublisher.publish_api_config_event(
            EventTypes.API_CONFIG_UPDATED,
            {
                'config_id': str(api_config.id),
                'name': api_config.name,
                'old_data': old_data,
                'new_data': {
                    'name': api_config.name,
                    'version': api_config.version,
                    'protocol': api_config.protocol,
                    'base_url': api_config.base_url,
                    'is_active': api_config.is_active
                }
            },
            str(request.user.id)
        )
        
        return Response(serializer.data)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        vendor_id = request.query_params.get('vendor')
        if vendor_id:
            queryset = queryset.filter(vendor_id=vendor_id)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def test_command(self, request, pk=None):
        api_config = self.get_object()
        command_type = request.data.get('command_type')
        params = request.data.get('params', {})
        
        start_time = time.time()
        try:
            command_template = CommandTemplate.objects.get(
                api_config=api_config,
                command_type=command_type
            )
            
            handler = get_protocol_handler(api_config.protocol)
            result = handler.execute_command(api_config, command_template, params)
            execution_time = time.time() - start_time
            
            # Publish command test event
            EventPublisher.publish_command_event(
                EventTypes.COMMAND_EXECUTED,
                {
                    'config_id': str(api_config.id),
                    'command_type': command_type,
                    'params': params,
                    'result': result,
                    'execution_time': execution_time,
                    'test_mode': True,
                    'user_id': str(request.user.id)
                }
            )
            
            return Response({
                'success': True,
                'result': result
            })
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_message = str(e)
            
            # Publish failed command test event
            EventPublisher.publish_command_event(
                EventTypes.COMMAND_FAILED,
                {
                    'config_id': str(api_config.id),
                    'command_type': command_type,
                    'params': params,
                    'error': error_message,
                    'execution_time': execution_time,
                    'test_mode': True,
                    'user_id': str(request.user.id)
                }
            )
            
            return Response({
                'success': False,
                'error': error_message
            }, status=400)
    
    @action(detail=False, methods=['get'], url_path='auth-methods')
    def auth_methods(self, request, pk=None):
        """
        Returns the list of supported authentication methods.
        """
        auth_methods = ({"value": code, "label": label} for code, label in AUTH_CHOICES)
        return Response(auth_methods, status=status.HTTP_200_OK)

class CommandTemplateViewSet(PermissionRequiredMixin, OrganizationFilterMixin, viewsets.ModelViewSet):
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'id']
    ordering_fields = ['name', 'created_at']
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
    
    def get_queryset(self):
        api_config_id = self.request.query_params.get('api_config')
        if api_config_id:
            return self.queryset.filter(api_config_id=api_config_id)
        return self.queryset
    
    def create(self, request, *args, **kwargs):
        """Create command template và publish event"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        command_template = serializer.save()
        
        # Publish command template created event
        EventPublisher.publish_api_config_event(
            'command_template_created',
            {
                'template_id': str(command_template.id),
                'command_type': command_template.command_type,
                'config_id': str(command_template.api_config.id),
                'config_name': command_template.api_config.name
            },
            str(request.user.id)
        )
        
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