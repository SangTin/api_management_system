from django.db import models
import uuid
from shared.models.constants import AUTH_CHOICES, HTTP_METHOD_CHOICES
from shared.models.base_config import BaseConfigurationMixin, BaseAuthMixin
from shared.models.soft_delete import SoftDeleteMixin, SoftDeleteManager

class APIConfiguration(SoftDeleteMixin, BaseAuthMixin, BaseConfigurationMixin):
    vendor = models.ForeignKey('vendor.Vendor', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    version = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = SoftDeleteManager()
    
    class Meta:
        db_table = 'api_configurations'
        unique_together = ['vendor', 'name', 'version']
        ordering = ['-created_at']
        default_manager_name = 'objects'

    def __str__(self):
        return f"{self.vendor.name} - {self.name} {self.version}"
    
    def soft_delete(self, user_id=None, reason=""):
        """Override to publish event"""
        super().soft_delete(user_id, reason)
        
        from shared.kafka.publisher import EventPublisher
        from shared.kafka.topics import Topics, EventTypes
        
        EventPublisher.publish_event(
            Topics.VENDOR_EVENTS,
            EventTypes.API_CONFIG_DELETED,
            {
                'api_config_id': str(self.id),
                'api_config_name': self.name,
                'version': self.version,
                'vendor_id': str(self.vendor.id) if self.vendor else None,
                'deleted_at': self.deleted_at.isoformat(),
                'deleted_by': str(self.deleted_by) if self.deleted_by else None,
                'deletion_reason': self.deletion_reason
            }
        )

class CommandTemplate(SoftDeleteMixin, BaseConfigurationMixin):
    api_config = models.ForeignKey(APIConfiguration, on_delete=models.CASCADE, null=True, blank=True)
    command_type = models.CharField(max_length=100)  # turn_on, turn_off, status, etc.
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Template Configuration
    url_template = models.CharField(max_length=500, blank=True, null=True)
    method = models.CharField(max_length=10, choices=HTTP_METHOD_CHOICES, default='POST')
    body_template = models.JSONField(default=dict)
    
    # Parameters
    required_params = models.JSONField(default=list)
    optional_params = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = SoftDeleteManager()

    class Meta:
        db_table = 'command_templates'
        unique_together = ['api_config', 'command_type']
        default_manager_name = 'objects'

    def __str__(self):
        return f"{self.api_config.name} - {self.command_type}"
    
    def soft_delete(self, user_id=None, reason=""):
        """Override to collect DeviceCommand data and publish event"""
        
        from device.models import DeviceCommand
        
        affected_device_commands = list(
            DeviceCommand.objects.filter(command=self)
            .select_related('device')
            .values(
                'id', 'device__id', 'device__name', 'device__serial_number',
                'is_primary', 'command_type', 'priority'
            )
        )
        
        super().soft_delete(user_id, reason)
        
        from shared.kafka.publisher import EventPublisher
        from shared.kafka.topics import Topics, EventTypes
        
        EventPublisher.publish_event(
            Topics.VENDOR_EVENTS,
            EventTypes.COMMAND_TEMPLATE_DELETED,
            {
                'template_id': str(self.id),
                'template_name': self.name,
                'command_type': self.command_type,
                'api_config_id': str(self.api_config.id) if self.api_config else None,
                'api_config_name': self.api_config.name if self.api_config else None,
                'deleted_at': self.deleted_at.isoformat(),
                'deleted_by': str(self.deleted_by) if self.deleted_by else None,
                'deletion_reason': self.deletion_reason,
                'affected_device_commands': affected_device_commands,
                'affected_count': len(affected_device_commands)
            }
        )