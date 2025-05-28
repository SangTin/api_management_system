from django.db import models
import uuid

class APIConfiguration(models.Model):
    PROTOCOL_CHOICES = [
        ('http', 'HTTP/HTTPS'),
        ('mqtt', 'MQTT'),
        ('tcp', 'TCP'),
        ('websocket', 'WebSocket'),
    ]

    AUTH_CHOICES = [
        ('none', 'No Authentication'),
        ('basic', 'Basic Authentication'),
        ('bearer', 'Bearer Token'),
        ('api_key', 'API Key'),
        ('oauth2', 'OAuth 2.0'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor = models.ForeignKey('vendor.Vendor', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    version = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    
    # Protocol Configuration
    protocol = models.CharField(max_length=20, choices=PROTOCOL_CHOICES)
    base_url = models.CharField(max_length=500)  # For HTTP/WebSocket
    host = models.CharField(max_length=200, blank=True)  # For TCP/MQTT
    port = models.IntegerField(null=True, blank=True)
    
    # Authentication Configuration
    auth_type = models.CharField(max_length=20, choices=AUTH_CHOICES)
    auth_config = models.JSONField(default=dict)  # username, password, token, etc.
    
    # Request Templates
    headers_template = models.JSONField(default=dict)
    request_template = models.JSONField(default=dict)
    
    # Command Mappings
    command_mappings = models.JSONField(default=dict)
    
    # Response Configuration
    response_mapping = models.JSONField(default=dict)
    success_indicators = models.JSONField(default=list)
    error_indicators = models.JSONField(default=list)
    
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

    def __str__(self):
        return f"{self.vendor.name} - {self.name} v{self.version}"

class CommandTemplate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    api_config = models.ForeignKey(APIConfiguration, on_delete=models.CASCADE)
    command_type = models.CharField(max_length=100)  # turn_on, turn_off, status, etc.
    display_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Template Configuration
    url_template = models.CharField(max_length=500)
    method = models.CharField(max_length=10, choices=[
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
        ('PATCH', 'PATCH'),
    ], default='POST')
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