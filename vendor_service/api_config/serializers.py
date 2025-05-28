from rest_framework import serializers
from .models import APIConfiguration, CommandTemplate

class CommandTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommandTemplate
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

class APIConfigurationSerializer(serializers.ModelSerializer):
    commands = CommandTemplateSerializer(many=True, read_only=True, source='commandtemplate_set')
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    
    class Meta:
        model = APIConfiguration
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')

    def create(self, validated_data):
        request = self.context['request']
        if not hasattr(request, 'user') or not hasattr(request.user, 'id'):
            raise serializers.ValidationError("User must be authenticated to create a vendor.")
        validated_data['created_by'] = request.user.id
        return super().create(validated_data)