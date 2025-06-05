from rest_framework import serializers
from .models import APIConfiguration, CommandTemplate
from vendor.models import Vendor
from vendor.serializers import SimpleVendorSerializer

class CommandTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommandTemplate
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

class APIConfigurationSerializer(serializers.ModelSerializer):
    vendor = SimpleVendorSerializer(read_only=True)
    
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