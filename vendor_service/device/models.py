from django.db import models
import uuid
from shared.models.base_config import BaseConfigurationMixin, BaseAuthMixin
from shared.models.soft_delete import SoftDeleteMixin, SoftDeleteManager

class Device(SoftDeleteMixin, BaseAuthMixin, BaseConfigurationMixin):
    name = models.CharField(max_length=255)
    vendor = models.ForeignKey('vendor.Vendor', on_delete=models.CASCADE, related_name='devices', null=True, blank=True)

    body_template = models.JSONField(default=dict, blank=True, null=True)
    params_template = models.JSONField(default=dict, blank=True, null=True)

    model = models.CharField(max_length=255, null=True, blank=True)
    serial_number = models.CharField(max_length=255, null=True, blank=True)
    firmware_version = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.UUIDField(default=uuid.uuid4, editable=False)
    
    objects = SoftDeleteManager()
    
    def __str__(self):
        return f"{self.name} ({self.serial_number or 'No Serial'})"

    class Meta:
        db_table = 'devices'
        unique_together = ('vendor', 'serial_number')
        ordering = ['-created_at']
        default_manager_name = 'objects'

class DeviceCommand(SoftDeleteMixin, BaseConfigurationMixin):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='command_templates')
    command = models.ForeignKey('api_config.CommandTemplate', on_delete=models.SET_NULL, related_name='device_command', null=True, blank=True)
    command_type = models.CharField(max_length=100)
    
    params = models.JSONField(default=dict, blank=True, null=True)
    
    is_primary = models.BooleanField(default=False)
    priority = models.IntegerField(default=1)
    
    is_active = models.BooleanField(default=True)  
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = SoftDeleteManager()
    
    class Meta:
        db_table = 'device_command'
        ordering = ['priority', '-created_at']
        indexes = [
            models.Index(fields=['device', 'command_type', 'priority']),
            models.Index(fields=['command_type']),
            models.Index(fields=['is_primary', 'is_active']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['device', 'command_type'],
                condition=models.Q(is_primary=True, is_active=True, is_deleted=False),
                name='unique_primary_device_command'
            )
        ]
        default_manager_name = 'objects'
        
    def __str__(self):
        primary = " (Primary)" if self.is_primary else ""
        return f"{self.device.name} - {self.command_type}{primary}"
        
    def save(self, *args, **kwargs):
        if self.command and not self.command_type:
            self.command_type = self.command.command_type

        super().save(*args, **kwargs)
        
    @classmethod
    def get_primary_command(cls, device_id, command_type):
        """Get primary command for execution"""
        return cls.objects.filter(
            device_id=device_id,
            command_type=command_type,
            is_primary=True,
            is_active=True
        ).first()