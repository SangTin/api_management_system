from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import APIConfiguration, CommandTemplate
from .serializers import APIConfigurationSerializer, CommandTemplateSerializer
from protocol_handlers import get_protocol_handler

class APIConfigurationViewSet(viewsets.ModelViewSet):
    queryset = APIConfiguration.objects.all()
    serializer_class = APIConfigurationSerializer

    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        api_config = self.get_object()
        handler = get_protocol_handler(api_config.protocol)
        
        try:
            result = handler.test_connection(api_config)
            return Response({
                'success': True,
                'message': 'Connection test successful',
                'details': result
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': 'Connection test failed',
                'error': str(e)
            }, status=400)

    @action(detail=True, methods=['post'])
    def test_command(self, request, pk=None):
        api_config = self.get_object()
        command_type = request.data.get('command_type')
        params = request.data.get('params', {})
        
        try:
            command_template = CommandTemplate.objects.get(
                api_config=api_config,
                command_type=command_type
            )
            
            handler = get_protocol_handler(api_config.protocol)
            result = handler.execute_command(api_config, command_template, params)
            
            return Response({
                'success': True,
                'result': result
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=400)

class CommandTemplateViewSet(viewsets.ModelViewSet):
    queryset = CommandTemplate.objects.all()
    serializer_class = CommandTemplateSerializer

    def get_queryset(self):
        api_config_id = self.request.query_params.get('api_config')
        if api_config_id:
            return self.queryset.filter(api_config_id=api_config_id)
        return self.queryset