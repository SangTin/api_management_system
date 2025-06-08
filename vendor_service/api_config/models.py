from django.db import models
import uuid
from shared.models.constants import AUTH_CHOICES, HTTP_METHOD_CHOICES
from shared.models.base_config import BaseConfigurationMixin, BaseAuthMixin

class APIConfiguration(BaseAuthMixin, BaseConfigurationMixin):
    vendor = models.ForeignKey('vendor.Vendor', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    version = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    created_by = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'api_configurations'
        unique_together = ['vendor', 'name', 'version']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.vendor.name} - {self.name} v{self.version}"

class CommandTemplate(BaseConfigurationMixin):
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

    class Meta:
        db_table = 'command_templates'
        unique_together = ['api_config', 'command_type']

    def __str__(self):
        return f"{self.api_config.name} - {self.command_type}"