from rest_framework import serializers
from .models import (
    DashboardMetrics, SystemHealthMetrics, UserActivityAnalytics,
    VendorPerformanceAnalytics, AlertRules, AlertInstance
)

class DashboardMetricsSerializer(serializers.ModelSerializer):
    success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = DashboardMetrics
        fields = [
            'id', 'metric_type', 'date', 'total_users', 'active_users',
            'new_users', 'user_logins', 'total_vendors', 'active_vendors',
            'new_vendors', 'total_api_configs', 'api_tests_executed',
            'api_tests_successful', 'commands_executed', 'commands_successful',
            'commands_failed', 'avg_response_time', 'system_errors',
            'system_warnings', 'success_rate', 'created_at', 'updated_at'
        ]
    
    def get_success_rate(self, obj):
        """Calculate command success rate"""
        total = obj.commands_executed + obj.commands_failed
        if total == 0:
            return 100.0
        return round((obj.commands_successful / total) * 100, 2)

class SystemHealthMetricsSerializer(serializers.ModelSerializer):
    overall_health_score = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemHealthMetrics
        fields = [
            'id', 'timestamp', 'user_service_status', 'vendor_service_status',
            'event_service_status', 'avg_api_response_time', 'error_rate',
            'cpu_usage', 'memory_usage', 'db_connections', 'db_query_time',
            'overall_health_score'
        ]
    
    def get_overall_health_score(self, obj):
        """Calculate overall health score"""
        services_up = sum([
            obj.user_service_status,
            obj.vendor_service_status,
            obj.event_service_status
        ])
        
        base_score = (services_up / 3) * 100
        
        # Penalize for high error rate and response time
        if obj.error_rate > 5:
            base_score -= 20
        elif obj.error_rate > 1:
            base_score -= 10
        
        if obj.avg_api_response_time > 1000:  # > 1 second
            base_score -= 15
        elif obj.avg_api_response_time > 500:  # > 500ms
            base_score -= 10
        
        return max(0, min(100, base_score))

class UserActivityAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivityAnalytics
        fields = [
            'id', 'date', 'hour', 'login_count', 'api_usage_count',
            'command_execution_count', 'unique_active_users',
            'avg_session_duration', 'created_at'
        ]

class VendorPerformanceAnalyticsSerializer(serializers.ModelSerializer):
    reliability_score = serializers.SerializerMethodField()
    
    class Meta:
        model = VendorPerformanceAnalytics
        fields = [
            'id', 'vendor_id', 'vendor_name', 'date', 'total_api_calls',
            'successful_api_calls', 'failed_api_calls', 'avg_response_time',
            'uptime_percentage', 'success_rate', 'unique_users',
            'total_devices', 'reliability_score', 'created_at', 'updated_at'
        ]
    
    def get_reliability_score(self, obj):
        """Calculate overall reliability score"""
        # Weighted average of success rate and uptime
        return round((obj.success_rate * 0.7) + (obj.uptime_percentage * 0.3), 2)

class AlertRulesSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertRules
        fields = [
            'id', 'name', 'description', 'alert_type', 'severity',
            'metric_name', 'threshold_value', 'comparison_operator',
            'is_active', 'cooldown_minutes', 'created_at', 'updated_at'
        ]

class AlertInstanceSerializer(serializers.ModelSerializer):
    alert_rule_name = serializers.CharField(source='alert_rule.name', read_only=True)
    alert_rule_severity = serializers.CharField(source='alert_rule.severity', read_only=True)
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = AlertInstance
        fields = [
            'id', 'alert_rule', 'alert_rule_name', 'alert_rule_severity',
            'triggered_at', 'resolved_at', 'status', 'triggered_value',
            'threshold_value', 'message', 'acknowledged_by',
            'acknowledged_at', 'resolution_notes', 'duration'
        ]
    
    def get_duration(self, obj):
        """Calculate alert duration in minutes"""
        if obj.resolved_at:
            delta = obj.resolved_at - obj.triggered_at
            return round(delta.total_seconds() / 60, 2)
        return None

class MetricsSummarySerializer(serializers.Serializer):
    """Serializer for summary statistics"""
    
    period_start = serializers.DateField()
    period_end = serializers.DateField()
    total_days = serializers.IntegerField()
    
    # User metrics
    total_logins = serializers.IntegerField()
    unique_users = serializers.IntegerField()
    avg_daily_logins = serializers.FloatField()
    
    # System metrics
    total_commands = serializers.IntegerField()
    successful_commands = serializers.IntegerField()
    failed_commands = serializers.IntegerField()
    success_rate = serializers.FloatField()
    
    # Performance metrics
    avg_response_time = serializers.FloatField()
    max_response_time = serializers.FloatField()
    min_response_time = serializers.FloatField()
    
    # Error metrics
    total_errors = serializers.IntegerField()
    total_warnings = serializers.IntegerField()
    error_rate = serializers.FloatField()

class TrendAnalysisSerializer(serializers.Serializer):
    """Serializer for trend analysis data"""
    
    metric_name = serializers.CharField()
    period = serializers.CharField()  # daily, weekly, monthly
    data_points = serializers.ListField(
        child=serializers.DictField()
    )
    trend_direction = serializers.CharField()  # up, down, stable
    trend_percentage = serializers.FloatField()
    
class ComparisonAnalysisSerializer(serializers.Serializer):
    """Serializer for period comparison analysis"""
    
    current_period = serializers.DictField()
    previous_period = serializers.DictField()
    comparison = serializers.DictField()
    insights = serializers.ListField(
        child=serializers.CharField()
    )