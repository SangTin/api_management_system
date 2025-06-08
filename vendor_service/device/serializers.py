from rest_framework import serializers
from .models import Device

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')

    def create(self, validated_data):
        request = self.context['request']
        if not hasattr(request, 'user') or not hasattr(request.user, 'id'):
            raise serializers.ValidationError("User must be authenticated to create a device.")
        validated_data['created_by'] = request.user.id
        return super().create(validated_data)