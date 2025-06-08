from django.db import models
import uuid
from shared.models.base_config import BaseConfigurationMixin, BaseAuthMixin

class Device(BaseAuthMixin, BaseConfigurationMixin):
    name = models.CharField(max_length=255)
    vendor = models.ForeignKey('vendor.Vendor', on_delete=models.CASCADE, related_name='devices', null=True, blank=True)

    body_template = models.JSONField(default=dict, blank=True, null=True)
    params_template = models.JSONField(default=dict, blank=True, null=True)

    model = models.CharField(max_length=255)
    serial_number = models.CharField(max_length=255, null=True, blank=True)
    firmware_version = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.UUIDField(default=uuid.uuid4, editable=False)
    
    def __str__(self):
        return f"{self.name} ({self.serial_number or 'No Serial'})"

    class Meta:
        db_table = 'devices'
        unique_together = ('vendor', 'serial_number')
        ordering = ['-created_at']

class DeviceCommandTemplate(BaseConfigurationMixin):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='command_templates')
    command = models.ForeignKey('api_config.CommandTemplate', on_delete=models.CASCADE, related_name='device_command_templates')
    
    params = models.JSONField(default=dict, blank=True, null=True)

    is_active = models.BooleanField(default=True)    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'device_command_templates'
        unique_together = ('device', 'command')
        
    def __str__(self):
        return f"{self.device.name} - {self.command.name} Template"