from django.db import models
import uuid
from django.utils import timezone

class EventLog(models.Model):
    """Model để lưu trữ các events từ Kafka"""
    
    EVENT_CATEGORIES = [
        ('user', 'User Events'),
        ('vendor', 'Vendor Events'),
        ('api_config', 'API Configuration Events'),
        ('command', 'Command Events'),
        ('system', 'System Events'),
        ('audit', 'Audit Events'),
    ]
    
    SEVERITY_LEVELS = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_id = models.CharField(max_length=100, unique=True)  # From Kafka message
    category = models.CharField(max_length=20, choices=EVENT_CATEGORIES)
    event_type = models.CharField(max_length=100)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='info')
    
    # Event data
    data = models.JSONField(default=dict)
    source_service = models.CharField(max_length=50)
    
    # Metadata
    user_id = models.CharField(max_length=100, blank=True, null=True)
    organization_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Timestamps
    event_timestamp = models.DateTimeField()  # When the event occurred
    processed_at = models.DateTimeField(auto_now_add=True)  # When we processed it
    
    class Meta:
        db_table = 'event_logs'
        indexes = [
            models.Index(fields=['category', 'event_type']),
            models.Index(fields=['event_timestamp']),
            models.Index(fields=['user_id']),
            models.Index(fields=['organization_id']),
            models.Index(fields=['severity']),
        ]
        ordering = ['-event_timestamp']
    
    def __str__(self):
        return f"{self.category}/{self.event_type} - {self.event_timestamp}"

class AuditLog(models.Model):
    """Model để lưu trữ audit trail"""
    
    ACTIONS = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('activate', 'Activate'),
        ('deactivate', 'Deactivate'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('access', 'Access'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Action details
    action = models.CharField(max_length=20, choices=ACTIONS)
    resource_type = models.CharField(max_length=50)  # vendor, api_config, user, etc.
    resource_id = models.CharField(max_length=100)
    
    # User info
    user_id = models.CharField(max_length=100)
    username = models.CharField(max_length=100, blank=True)
    organization_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Change details
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    
    # Request details
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamp
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['action', 'resource_type']),
            models.Index(fields=['user_id']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['resource_type', 'resource_id']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.user_id} {self.action} {self.resource_type}:{self.resource_id}"

class CommandExecutionLog(models.Model):
    """Model để lưu trữ chi tiết command execution"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('executing', 'Executing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('timeout', 'Timeout'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Command details
    device_id = models.CharField(max_length=100)
    command_type = models.CharField(max_length=100)
    command_params = models.JSONField(default=dict)
    
    # Execution details
    api_config_id = models.CharField(max_length=100)
    protocol = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    
    # Results
    result = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    
    # Performance metrics
    execution_time = models.FloatField(null=True, blank=True)  # seconds
    response_size = models.IntegerField(null=True, blank=True)  # bytes
    
    # User context
    user_id = models.CharField(max_length=100, blank=True, null=True)
    test_mode = models.BooleanField(default=False)
    
    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'command_execution_logs'
        indexes = [
            models.Index(fields=['device_id']),
            models.Index(fields=['status']),
            models.Index(fields=['requested_at']),
            models.Index(fields=['user_id']),
            models.Index(fields=['api_config_id']),
        ]
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"{self.command_type} on {self.device_id} - {self.status}"

class SystemMetrics(models.Model):
    """Model để lưu trữ system metrics từ events"""
    
    METRIC_TYPES = [
        ('api_response_time', 'API Response Time'),
        ('command_success_rate', 'Command Success Rate'),
        ('user_activity', 'User Activity'),
        ('system_health', 'System Health'),
        ('error_rate', 'Error Rate'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Metric details
    metric_type = models.CharField(max_length=50, choices=METRIC_TYPES)
    metric_name = models.CharField(max_length=100)
    value = models.FloatField()
    unit = models.CharField(max_length=20, blank=True)  # ms, %, count, etc.
    
    # Context
    source_service = models.CharField(max_length=50)
    tags = models.JSONField(default=dict)  # Additional metadata
    
    # Time
    timestamp = models.DateTimeField(auto_now_add=True)
    period_start = models.DateTimeField(null=True, blank=True)  # For aggregated metrics
    period_end = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'system_metrics'
        indexes = [
            models.Index(fields=['metric_type', 'timestamp']),
            models.Index(fields=['source_service']),
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.metric_name}: {self.value} {self.unit}"