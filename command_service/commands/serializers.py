from rest_framework import serializers
from .models import CommandRequest, CommandExecution

class CommandExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommandExecution
        fields = [
            'id', 'agent_id', 'api_config_id', 'protocol',
            'result', 'error_message', 'response_data',
            'execution_time', 'response_size',
            'started_at', 'completed_at'
        ]
        read_only_fields = ['id']

class CommandRequestSerializer(serializers.ModelSerializer):
    execution = CommandExecutionSerializer(read_only=True, source='commandexecution_set.first')
    
    class Meta:
        model = CommandRequest
        fields = [
            'id', 'device_id', 'command_type', 'command_params',
            'user_id', 'scheduled_at', 'retry_count', 'max_retries',
            'status', 'created_at', 'updated_at', 'execution'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class CommandRequestCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating command requests"""
    
    class Meta:
        model = CommandRequest
        fields = [
            'device_id', 'command_type', 'command_params',
            'user_id', 'scheduled_at', 'max_retries'
        ]
        
    def validate(self, data):
        """Validate command request data"""
        # Basic validation
        if not data.get('device_id'):
            raise serializers.ValidationError("device_id is required")
        
        if not data.get('command_type'):
            raise serializers.ValidationError("command_type is required")
            
        return data