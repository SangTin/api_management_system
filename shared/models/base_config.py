from .constants import AUTH_CHOICES, HTTP_METHOD_CHOICES
import uuid
from django.db import models

class BaseConfigurationMixin(models.Model):
    """Base mixin cho tất cả configuration classes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Network & Connection
    base_url = models.CharField(max_length=500, null=True, blank=True)
    timeout = models.IntegerField(null=True, blank=True, default=30)
    retry_count = models.IntegerField(null=True, blank=True, default=3)
    retry_delay = models.IntegerField(null=True, blank=True, default=5)
    
    # Headers & Request config
    headers_template = models.JSONField(default=dict, blank=True)
    
    class Meta:
        abstract = True
    
    def get_effective_config(self):
        """Get effective configuration after inheritance"""
        return {
            'base_url': self.base_url,
            'timeout': self.timeout or 30,
            'retry_count': self.retry_count or 3,
            'retry_delay': self.retry_delay or 5,
            'auth_type': self.auth_type or 'none',
            'auth_config': self.auth_config or {},
            'headers_template': self.headers_template or {},
        }
        
class BaseAuthMixin(models.Model):
    """Base mixin cho các authentication classes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Authentication
    auth_type = models.CharField(max_length=20, choices=AUTH_CHOICES, default='none')
    auth_config = models.JSONField(default=dict, blank=True)
    
    class Meta:
        abstract = True
    
    def get_auth_config(self):
        """Get authentication configuration"""
        return {
            'auth_type': self.auth_type or 'none',
            'auth_config': self.auth_config or {},
        }