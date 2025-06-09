from rest_framework import serializers
from .models import Device, DeviceCommand
from vendor.serializers import SimpleVendorSerializer
from api_config.serializers import CommandTemplateSerializer
from api_config.models import CommandTemplate
from vendor.models import Vendor

class SimpleDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ['id', 'name']
    
class DeviceCommandSerializer(serializers.ModelSerializer):
    device = SimpleDeviceSerializer(read_only=True)
    device_id = serializers.PrimaryKeyRelatedField(
        queryset=Device.objects.all(),
        source='device',
        write_only=True,
        allow_null=True,
        required=False,
        default=None
    )
    command = CommandTemplateSerializer(read_only=True)
    command_id = serializers.PrimaryKeyRelatedField(
        queryset=CommandTemplate.objects.all(),
        source='command',
        write_only=True,
        allow_null=True,
        required=False,
        default=None
    )
    
    class Meta:
        model = DeviceCommand
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        request = self.context['request']
        if not hasattr(request, 'user') or not hasattr(request.user, 'id'):
            raise serializers.ValidationError("User must be authenticated to create a command template.")
        validated_data['created_by'] = request.user.id
        return super().create(validated_data)

class DeviceSerializer(serializers.ModelSerializer):
    vendor = SimpleVendorSerializer(read_only=True)
    vendor_id = serializers.PrimaryKeyRelatedField(
        queryset=Vendor.objects.all(),
        source='vendor',
        write_only=True,
        allow_null=True,
        required=False,
        default=None
    )
    command_ids = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(
            queryset=CommandTemplate.objects.all()
        ),
        write_only=True,
        required=False
    )
    commands = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Device
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')

    def get_commands(self, obj):
        return [str(dc.command_id) for dc in obj.command_templates.all()]

    def create(self, validated_data):
        command_list = validated_data.pop('command_ids', [])
        request = self.context['request']

        if not hasattr(request, 'user') or not hasattr(request.user, 'id'):
            raise serializers.ValidationError("User must be authenticated to create a device.")

        validated_data['created_by'] = request.user.id
        device = super().create(validated_data)

        self._sync_device_commands(device, command_list, request.user.id)
        return device

    def update(self, instance, validated_data):
        command_list = validated_data.pop('command_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if command_list is not None:
            self._sync_device_commands(instance, command_list, self.context['request'].user.id)

        return instance

    def _sync_device_commands(self, device, command_list, user_id):
        existing_commands = {
            str(dc.command_id): dc for dc in device.command_templates.with_deleted()
        }
        new_command_ids = set(str(cmd.id) for cmd in command_list)

        for cmd in command_list:
            cid = str(cmd.id)
            if cid in existing_commands:
                dc = existing_commands[cid]
                if getattr(dc, 'is_deleted', False):
                    dc.restore()
                dc.save()
            else:
                DeviceCommand.objects.create(device=device, command=cmd)
            print(f"Processed command: {cid} for device: {device.name}")

        for cid, dc in existing_commands.items():
            if cid not in new_command_ids and not getattr(dc, 'is_deleted', False):
                dc.soft_delete(user_id=user_id, reason="Removed from update")