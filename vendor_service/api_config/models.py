from django.db import models
import uuid
from .constants import AUTH_CHOICES, HTTP_METHOD_CHOICES

class APIConfiguration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey('vendor.Vendor', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    version = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    base_url = models.CharField(max_length=500)

    # Authentication Configuration
    auth_type = models.CharField(max_length=20, choices=AUTH_CHOICES)
    auth_config = models.JSONField(default=dict)  # username, password, token, etc.
    
    # Request Templates
    headers_template = models.JSONField(default=dict)
    
    # Settings
    timeout = models.IntegerField(default=30)  # seconds
    retry_count = models.IntegerField(default=3)
    retry_delay = models.IntegerField(default=5)  # seconds
    
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

class CommandTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    api_config = models.ForeignKey(APIConfiguration, on_delete=models.CASCADE)
    command_type = models.CharField(max_length=100)  # turn_on, turn_off, status, etc.
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Template Configuration
    url_template = models.CharField(max_length=500)
    method = models.CharField(max_length=10, choices=HTTP_METHOD_CHOICES, default='POST')
    headers_template = models.JSONField(default=dict)
    body_template = models.JSONField(default=dict)
    
    # Parameters
    required_params = models.JSONField(default=list)
    optional_params = models.JSONField(default=list)
    
    # Response Processing
    response_path = models.CharField(max_length=200, blank=True)  # JSONPath for result
    success_condition = models.CharField(max_length=500, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'command_templates'
        unique_together = ['api_config', 'command_type']

    def __str__(self):
        return f"{self.api_config.name} - {self.command_type}"