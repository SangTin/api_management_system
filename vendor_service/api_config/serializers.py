from rest_framework import serializers
from .models import APIConfiguration, CommandTemplate
from vendor.models import Vendor
from vendor.serializers import SimpleVendorSerializer
from shared.models.decorators import force_overwrite_auth

class SimpleAPIConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = APIConfiguration
        fields = ('id', 'name')
        read_only_fields = ('id', 'name')

class CommandTemplateSerializer(serializers.ModelSerializer):
    api_config = SimpleAPIConfigurationSerializer(read_only=True)
    api_config_id = serializers.PrimaryKeyRelatedField(
        queryset=APIConfiguration.objects.all(),
        source='api_config',
        write_only=True,
        allow_null=True,
        required=False
    )
    
    class Meta:
        model = CommandTemplate
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

class APIConfigurationSerializer(serializers.ModelSerializer):
    vendor = SimpleVendorSerializer(read_only=True)
    vendor_id = serializers.PrimaryKeyRelatedField(
        queryset=Vendor.objects.all(),
        source='vendor',
        write_only=True,
        allow_null=True,
        required=False,
        default=None
    )
    
    class Meta:
        model = APIConfiguration
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')
        
    @force_overwrite_auth(auth_field="auth_config")
    def create(self, validated_data):
        request = self.context['request']
        if not hasattr(request, 'user') or not hasattr(request.user, 'id'):
            raise serializers.ValidationError("User must be authenticated to create an API configuration.")
        validated_data['created_by'] = request.user.id
        return super().create(validated_data)
    
    @force_overwrite_auth(auth_field="auth_config")
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)
    
    def to_representation(self, instance):
        rep = super().to_representation(instance)

        auth_type = rep.get("auth_type")
        config = instance.auth_config or {}

        if auth_type == "bearer":
            rep["auth_config"] = {
                "token": "__HIDDEN__" if config.get("token") else "",
            }
        elif auth_type == "api_key":
            rep["auth_config"] = {
                "key_name": config.get("key_name", ""),
                "api_key": "__HIDDEN__" if config.get("api_key") else "",
            }
        elif auth_type == "basic":
            rep["auth_config"] = {
                "username": config.get("username", ""),
                "password": "__HIDDEN__" if config.get("password") else ""
            }
        else:
            rep["auth_config"] = {}

        return rep