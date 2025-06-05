from django.db import models
import uuid
from django.utils import timezone
from datetime import timedelta

class DashboardMetrics(models.Model):
    """Model để lưu metrics tổng hợp cho dashboard"""
    
    METRIC_TYPES = [
        ('daily', 'Daily Metrics'),
        ('weekly', 'Weekly Metrics'),
        ('monthly', 'Monthly Metrics'),
        ('real_time', 'Real Time Metrics'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPES)
    date = models.DateField()
    
    # User metrics
    total_users = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    new_users = models.IntegerField(default=0)
    user_logins = models.IntegerField(default=0)
    
    # Vendor metrics
    total_vendors = models.IntegerField(default=0)
    active_vendors = models.IntegerField(default=0)
    new_vendors = models.IntegerField(default=0)
    
    # API metrics
    total_api_configs = models.IntegerField(default=0)
    api_tests_executed = models.IntegerField(default=0)
    api_tests_successful = models.IntegerField(default=0)
    
    # Command metrics
    commands_executed = models.IntegerField(default=0)
    commands_successful = models.IntegerField(default=0)
    commands_failed = models.IntegerField(default=0)
    avg_response_time = models.FloatField(default=0.0)  # milliseconds
    
    # System metrics
    system_errors = models.IntegerField(default=0)
    system_warnings = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'dashboard_metrics'
        unique_together = ['metric_type', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.metric_type} metrics for {self.date}"

class SystemHealthMetrics(models.Model):
    """Model để track system health theo thời gian"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Service availability
    user_service_status = models.BooleanField(default=True)
    vendor_service_status = models.BooleanField(default=True)
    event_service_status = models.BooleanField(default=True)
    
    # Performance metrics
    avg_api_response_time = models.FloatField(default=0.0)  # ms
    error_rate = models.FloatField(default=0.0)  # percentage
    
    # Resource usage (if available)
    cpu_usage = models.FloatField(null=True, blank=True)  # percentage
    memory_usage = models.FloatField(null=True, blank=True)  # percentage
    
    # Database metrics
    db_connections = models.IntegerField(null=True, blank=True)
    db_query_time = models.FloatField(null=True, blank=True)  # ms
    
    class Meta:
        db_table = 'system_health_metrics'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"Health metrics at {self.timestamp}"

class UserActivityAnalytics(models.Model):
    """Model để phân tích user activity patterns"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField()
    hour = models.IntegerField()  # 0-23
    
    # Activity counts by hour
    login_count = models.IntegerField(default=0)
    api_usage_count = models.IntegerField(default=0)
    command_execution_count = models.IntegerField(default=0)
    
    # User behavior
    unique_active_users = models.IntegerField(default=0)
    avg_session_duration = models.FloatField(default=0.0)  # minutes
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_activity_analytics'
        unique_together = ['date', 'hour']
        ordering = ['-date', '-hour']
    
    def __str__(self):
        return f"User activity {self.date} {self.hour}:00"

class VendorPerformanceAnalytics(models.Model):
    """Model để phân tích performance của từng vendor"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vendor_id = models.CharField(max_length=100)
    vendor_name = models.CharField(max_length=200)
    date = models.DateField()
    
    # API performance
    total_api_calls = models.IntegerField(default=0)
    successful_api_calls = models.IntegerField(default=0)
    failed_api_calls = models.IntegerField(default=0)
    avg_response_time = models.FloatField(default=0.0)  # ms
    
    # Reliability metrics
    uptime_percentage = models.FloatField(default=100.0)
    success_rate = models.FloatField(default=100.0)
    
    # Usage metrics
    unique_users = models.IntegerField(default=0)
    total_devices = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'vendor_performance_analytics'
        unique_together = ['vendor_id', 'date']
        ordering = ['-date', 'vendor_name']
    
    def __str__(self):
        return f"{self.vendor_name} performance for {self.date}"

class AlertRules(models.Model):
    """Model để định nghĩa các alert rules"""
    
    ALERT_TYPES = [
        ('threshold', 'Threshold Alert'),
        ('anomaly', 'Anomaly Detection'),
        ('trend', 'Trend Alert'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS)
    
    # Rule configuration
    metric_name = models.CharField(max_length=100)  # error_rate, response_time, etc.
    threshold_value = models.FloatField()
    comparison_operator = models.CharField(max_length=10)  # >, <, >=, <=, ==
    
    # Alert settings
    is_active = models.BooleanField(default=True)
    cooldown_minutes = models.IntegerField(default=30)  # Avoid spam
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'alert_rules'
        ordering = ['severity', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.severity})"

class AlertInstance(models.Model):
    """Model để lưu các alert instances đã được trigger"""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    alert_rule = models.ForeignKey(AlertRules, on_delete=models.CASCADE)
    
    # Alert details
    triggered_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Alert context
    triggered_value = models.FloatField()
    threshold_value = models.FloatField()
    message = models.TextField()
    
    # Response tracking
    acknowledged_by = models.CharField(max_length=100, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolution_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'alert_instances'
        ordering = ['-triggered_at']
    
    def __str__(self):
        return f"{self.alert_rule.name} - {self.status}"