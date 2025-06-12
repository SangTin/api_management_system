from django.db import models
import uuid

class CommandRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    device_id = models.CharField(max_length=100)
    command_type = models.CharField(max_length=100)
    command_params = models.JSONField(default=dict)
    
    # Request context
    user_id = models.CharField(max_length=100)
    
    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=3)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=[
        ('queued', 'Queued'),
        ('executing', 'Executing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('timeout', 'Timeout'),
        ('cancelled', 'Cancelled')
    ], default='queued')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.command_type} on {self.device_id}"

class CommandExecution(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    command_request = models.ForeignKey(CommandRequest, on_delete=models.CASCADE, related_name='executions')
    
    # Execution details
    agent_id = models.CharField(max_length=100)
    api_config_id = models.CharField(max_length=100, null=True, blank=True)
    protocol = models.CharField(max_length=20)
    
    # Results
    result = models.JSONField(default=dict)
    error_message = models.TextField(blank=True)
    response_data = models.JSONField(default=dict, null=True, blank=True)
    
    # Performance
    execution_time = models.FloatField(default=0.0)
    response_size = models.IntegerField(null=True, blank=True)
    
    # Timestamps
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField()

    def __str__(self):
        return f"Execution of {self.command_request.command_type} ({self.id})"