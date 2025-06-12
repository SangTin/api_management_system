from rest_framework import serializers
from .models import CommandRequest, CommandExecution

class CommandRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommandRequest
        fields = '__all__'
        read_only_fields = ('id', 'status', 'created_at', 'updated_at')

class CommandExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommandExecution
        fields = '__all__'
        read_only_fields = ('id', 'started_at', 'completed_at')