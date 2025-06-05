import csv
import json
from io import StringIO
from datetime import datetime, timedelta
from django.db.models import Count, Avg, Sum, Q, F
from django.http import HttpResponse
from django.utils import timezone
from events.models import EventLog, AuditLog, CommandExecutionLog, SystemMetrics
from .models import DashboardMetrics, SystemHealthMetrics, VendorPerformanceAnalytics

class AnalyticsService:
    """Service class để xử lý analytics logic"""
    
    def get_dashboard_overview(self, start_date, end_date):
        """Get overview metrics cho dashboard"""
        
        # User metrics
        user_events = EventLog.objects.filter(
            category='user',
            event_timestamp__date__gte=start_date,
            event_timestamp__date__lte=end_date
        )
        
        user_logins = user_events.filter(event_type='user_login').count()
        unique_users = user_events.values('user_id').distinct().count()
        
        # Vendor metrics
        vendor_events = EventLog.objects.filter(
            category='vendor',
            event_timestamp__date__gte=start_date,
            event_timestamp__date__lte=end_date
        )
        
        vendors_created = vendor_events.filter(event_type='vendor_created').count()
        vendors_updated = vendor_events.filter(event_type='vendor_updated').count()
        
        # Command metrics
        command_events = EventLog.objects.filter(
            category='command',
            event_timestamp__date__gte=start_date,
            event_timestamp__date__lte=end_date
        )
        
        commands_executed = command_events.filter(event_type='command_executed').count()
        commands_failed = command_events.filter(event_type='command_failed').count()
        
        success_rate = 0
        if commands_executed + commands_failed > 0:
            success_rate = (commands_executed / (commands_executed + commands_failed)) * 100
        
        # System metrics
        system_events = EventLog.objects.filter(
            category='system',
            event_timestamp__date__gte=start_date,
            event_timestamp__date__lte=end_date
        )
        
        system_errors = system_events.filter(severity='error').count()
        system_warnings = system_events.filter(severity='warning').count()
        
        # Response time metrics
        response_metrics = SystemMetrics.objects.filter(
            metric_type='api_response_time',
            timestamp__date__gte=start_date,
            timestamp__date__lte=end_date
        ).aggregate(avg_time=Avg('value'))
        
        avg_response_time = response_metrics['avg_time'] or 0
        
        return {
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'days': (end_date - start_date).days + 1
            },
            'users': {
                'total_logins': user_logins,
                'unique_users': unique_users,
                'avg_logins_per_day': user_logins / ((end_date - start_date).days + 1)
            },
            'vendors': {
                'created': vendors_created,
                'updated': vendors_updated,
                'total_activities': vendors_created + vendors_updated
            },
            'commands': {
                'executed': commands_executed,
                'failed': commands_failed,
                'success_rate': round(success_rate, 2),
                'total': commands_executed + commands_failed
            },
            'system': {
                'errors': system_errors,
                'warnings': system_warnings,
                'avg_response_time': round(avg_response_time, 2)
            },
            'generated_at': timezone.now().isoformat()
        }
    
    def get_user_analytics(self, start_date, end_date):
        """Get detailed user analytics"""
        
        # Daily user activity
        daily_activity = []
        current_date = start_date
        
        while current_date <= end_date:
            day_events = EventLog.objects.filter(
                category='user',
                event_timestamp__date=current_date
            )
            
            logins = day_events.filter(event_type='user_login').count()
            unique_users = day_events.values('user_id').distinct().count()
            
            daily_activity.append({
                'date': current_date.isoformat(),
                'logins': logins,
                'unique_users': unique_users
            })
            
            current_date += timedelta(days=1)
        
        # Hourly patterns (for last 7 days)
        seven_days_ago = end_date - timedelta(days=7)
        hourly_pattern = []
        
        for hour in range(24):
            hour_logins = EventLog.objects.filter(
                category='user',
                event_type='user_login',
                event_timestamp__date__gte=seven_days_ago,
                event_timestamp__date__lte=end_date,
                event_timestamp__hour=hour
            ).count()
            
            hourly_pattern.append({
                'hour': hour,
                'logins': hour_logins
            })
        
        # Top active users
        top_users = EventLog.objects.filter(
            category='user',
            event_timestamp__date__gte=start_date,
            event_timestamp__date__lte=end_date,
            user_id__isnull=False
        ).values('user_id').annotate(
            activity_count=Count('id')
        ).order_by('-activity_count')[:10]
        
        return {
            'daily_activity': daily_activity,
            'hourly_pattern': hourly_pattern,
            'top_users': list(top_users),
            'summary': {
                'total_period_days': (end_date - start_date).days + 1,
                'avg_daily_logins': sum(day['logins'] for day in daily_activity) / len(daily_activity),
                'peak_hour': max(hourly_pattern, key=lambda x: x['logins'])['hour']
            }
        }
    
    def get_vendor_performance(self, start_date, end_date, vendor_id=None):
        """Get vendor performance analytics"""
        
        vendor_filter = Q(category='vendor')
        if vendor_id:
            vendor_filter &= Q(data__vendor__vendor_id=vendor_id)
        
        vendor_events = EventLog.objects.filter(
            vendor_filter,
            event_timestamp__date__gte=start_date,
            event_timestamp__date__lte=end_date
        )
        
        # API performance by vendor
        api_events = EventLog.objects.filter(
            category='api_config',
            event_timestamp__date__gte=start_date,
            event_timestamp__date__lte=end_date
        )
        
        vendor_performance = []
        
        # Get unique vendors from events
        vendors = vendor_events.values('data__vendor__vendor_id', 'data__vendor__name').distinct()
        
        for vendor in vendors:
            vendor_id = vendor['data__vendor__vendor_id']
            vendor_name = vendor['data__vendor__name']
            
            if not vendor_id or not vendor_name:
                continue
            
            # API calls for this vendor
            vendor_api_events = api_events.filter(
                data__vendor_id=vendor_id
            )
            
            tests_executed = vendor_api_events.filter(event_type='api_config_tested').count()
            
            # Command execution for this vendor's devices
            command_events = EventLog.objects.filter(
                category='command',
                event_timestamp__date__gte=start_date,
                event_timestamp__date__lte=end_date,
                data__config_id__in=api_events.filter(
                    data__vendor_id=vendor_id
                ).values('data__config_id')
            )
            
            commands_executed = command_events.filter(event_type='command_executed').count()
            commands_failed = command_events.filter(event_type='command_failed').count()
            
            success_rate = 0
            if commands_executed + commands_failed > 0:
                success_rate = (commands_executed / (commands_executed + commands_failed)) * 100
            
            vendor_performance.append({
                'vendor_id': vendor_id,
                'vendor_name': vendor_name,
                'api_tests': tests_executed,
                'commands_executed': commands_executed,
                'commands_failed': commands_failed,
                'success_rate': round(success_rate, 2)
            })
        
        return {
            'vendor_performance': vendor_performance,
            'summary': {
                'total_vendors': len(vendor_performance),
                'avg_success_rate': round(
                    sum(v['success_rate'] for v in vendor_performance) / len(vendor_performance) 
                    if vendor_performance else 0, 2
                )
            }
        }
    
    def get_system_health(self, start_time, end_time):
        """Get system health metrics"""
        
        # Error rate over time
        error_events = EventLog.objects.filter(
            severity='error',
            event_timestamp__gte=start_time,
            event_timestamp__lte=end_time
        )
        
        warning_events = EventLog.objects.filter(
            severity='warning',
            event_timestamp__gte=start_time,
            event_timestamp__lte=end_time
        )
        
        # Service status
        services = ['user-service', 'vendor-service', 'event-service']
        service_health = []
        
        for service in services:
            service_errors = error_events.filter(source_service=service).count()
            service_warnings = warning_events.filter(source_service=service).count()
            
            # Simple health calculation
            health_score = max(0, 100 - (service_errors * 10) - (service_warnings * 2))
            
            service_health.append({
                'service': service,
                'health_score': health_score,
                'errors': service_errors,
                'warnings': service_warnings,
                'status': 'healthy' if health_score >= 80 else 'degraded' if health_score >= 50 else 'unhealthy'
            })
        
        # Response time trends
        response_metrics = SystemMetrics.objects.filter(
            metric_type='api_response_time',
            timestamp__gte=start_time,
            timestamp__lte=end_time
        ).order_by('timestamp')
        
        response_trends = []
        for metric in response_metrics:
            response_trends.append({
                'timestamp': metric.timestamp.isoformat(),
                'response_time': metric.value
            })
        
        return {
            'service_health': service_health,
            'response_trends': response_trends,
            'overall_health': {
                'score': round(sum(s['health_score'] for s in service_health) / len(service_health), 2),
                'total_errors': error_events.count(),
                'total_warnings': warning_events.count()
            }
        }
    
    def get_command_analytics(self, start_date, end_date, device_id=None):
        """Get command execution analytics"""
        
        command_filter = Q(category='command')
        if device_id:
            command_filter &= Q(data__device_id=device_id)
        
        command_events = EventLog.objects.filter(
            command_filter,
            event_timestamp__date__gte=start_date,
            event_timestamp__date__lte=end_date
        )
        
        # Command types analysis
        command_types = command_events.values('data__command_type').annotate(
            total=Count('id'),
            executed=Count('id', filter=Q(event_type='command_executed')),
            failed=Count('id', filter=Q(event_type='command_failed'))
        ).order_by('-total')
        
        # Daily command volume
        daily_commands = []
        current_date = start_date
        
        while current_date <= end_date:
            day_commands = command_events.filter(event_timestamp__date=current_date)
            executed = day_commands.filter(event_type='command_executed').count()
            failed = day_commands.filter(event_type='command_failed').count()
            
            daily_commands.append({
                'date': current_date.isoformat(),
                'executed': executed,
                'failed': failed,
                'total': executed + failed
            })
            
            current_date += timedelta(days=1)
        
        # Response time analysis
        execution_logs = CommandExecutionLog.objects.filter(
            requested_at__date__gte=start_date,
            requested_at__date__lte=end_date,
            execution_time__isnull=False
        )
        
        if device_id:
            execution_logs = execution_logs.filter(device_id=device_id)
        
        avg_execution_time = execution_logs.aggregate(avg_time=Avg('execution_time'))['avg_time'] or 0
        
        return {
            'command_types': list(command_types),
            'daily_commands': daily_commands,
            'summary': {
                'total_commands': command_events.count(),
                'success_rate': round(
                    (command_events.filter(event_type='command_executed').count() / 
                     command_events.count() * 100) if command_events.count() > 0 else 0, 2
                ),
                'avg_execution_time': round(avg_execution_time, 3),
                'most_used_command': command_types[0]['data__command_type'] if command_types else None
            }
        }
    
    def get_real_time_metrics(self, start_time, end_time):
        """Get real-time metrics for last hour"""
        
        # Recent events
        recent_events = EventLog.objects.filter(
            event_timestamp__gte=start_time,
            event_timestamp__lte=end_time
        ).order_by('-event_timestamp')[:20]
        
        # Current active users (users with activity in last hour)
        active_users = EventLog.objects.filter(
            category='user',
            event_timestamp__gte=start_time,
            event_timestamp__lte=end_time,
            user_id__isnull=False
        ).values('user_id').distinct().count()
        
        # Commands per minute (last 60 minutes)
        commands_per_minute = []
        current_time = end_time
        
        for i in range(60):
            minute_start = current_time - timedelta(minutes=i+1)
            minute_end = current_time - timedelta(minutes=i)
            
            minute_commands = EventLog.objects.filter(
                category='command',
                event_timestamp__gte=minute_start,
                event_timestamp__lt=minute_end
            ).count()
            
            commands_per_minute.append({
                'timestamp': minute_start.isoformat(),
                'commands': minute_commands
            })
        
        commands_per_minute.reverse()  # Chronological order
        
        # System errors in last hour
        recent_errors = EventLog.objects.filter(
            severity='error',
            event_timestamp__gte=start_time,
            event_timestamp__lte=end_time
        ).count()
        
        # API response times
        recent_response_times = SystemMetrics.objects.filter(
            metric_type='api_response_time',
            timestamp__gte=start_time,
            timestamp__lte=end_time
        ).aggregate(
            avg_time=Avg('value'),
            max_time=models.Max('value'),
            min_time=models.Min('value')
        )
        
        return {
            'current_time': timezone.now().isoformat(),
            'active_users': active_users,
            'recent_errors': recent_errors,
            'commands_per_minute': commands_per_minute,
            'response_times': {
                'avg': round(recent_response_times['avg_time'] or 0, 2),
                'max': round(recent_response_times['max_time'] or 0, 2),
                'min': round(recent_response_times['min_time'] or 0, 2)
            },
            'recent_events': [
                {
                    'timestamp': event.event_timestamp.isoformat(),
                    'category': event.category,
                    'event_type': event.event_type,
                    'severity': event.severity,
                    'source_service': event.source_service
                }
                for event in recent_events
            ]
        }
    
    def calculate_daily_metrics(self, date):
        """Calculate and store daily metrics"""
        
        day_start = timezone.make_aware(datetime.combine(date, datetime.min.time()))
        day_end = timezone.make_aware(datetime.combine(date, datetime.max.time()))
        
        # User metrics
        user_events = EventLog.objects.filter(
            category='user',
            event_timestamp__gte=day_start,
            event_timestamp__lte=day_end
        )
        
        user_logins = user_events.filter(event_type='user_login').count()
        unique_users = user_events.values('user_id').distinct().count()
        
        # Vendor metrics
        vendor_events = EventLog.objects.filter(
            category='vendor',
            event_timestamp__gte=day_start,
            event_timestamp__lte=day_end
        )
        
        new_vendors = vendor_events.filter(event_type='vendor_created').count()
        
        # API metrics
        api_events = EventLog.objects.filter(
            category='api_config',
            event_timestamp__gte=day_start,
            event_timestamp__lte=day_end
        )
        
        api_tests = api_events.filter(event_type='api_config_tested').count()
        
        # Command metrics
        command_events = EventLog.objects.filter(
            category='command',
            event_timestamp__gte=day_start,
            event_timestamp__lte=day_end
        )
        
        commands_executed = command_events.filter(event_type='command_executed').count()
        commands_failed = command_events.filter(event_type='command_failed').count()
        
        # System metrics
        system_events = EventLog.objects.filter(
            category='system',
            event_timestamp__gte=day_start,
            event_timestamp__lte=day_end
        )
        
        system_errors = system_events.filter(severity='error').count()
        system_warnings = system_events.filter(severity='warning').count()
        
        # Response time
        response_metrics = SystemMetrics.objects.filter(
            metric_type='api_response_time',
            timestamp__gte=day_start,
            timestamp__lte=day_end
        ).aggregate(avg_time=Avg('value'))
        
        avg_response_time = response_metrics['avg_time'] or 0
        
        # Create or update daily metrics
        metrics, created = DashboardMetrics.objects.update_or_create(
            metric_type='daily',
            date=date,
            defaults={
                'user_logins': user_logins,
                'active_users': unique_users,
                'new_vendors': new_vendors,
                'api_tests_executed': api_tests,
                'commands_executed': commands_executed,
                'commands_failed': commands_failed,
                'avg_response_time': avg_response_time,
                'system_errors': system_errors,
                'system_warnings': system_warnings
            }
        )
        
        return metrics
    
    def export_to_csv(self, start_date, end_date):
        """Export analytics data to CSV"""
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="analytics_{start_date}_{end_date}.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'Date', 'User Logins', 'Active Users', 'New Vendors',
            'API Tests', 'Commands Executed', 'Commands Failed',
            'Success Rate', 'Avg Response Time', 'System Errors'
        ])
        
        # Write data
        metrics = DashboardMetrics.objects.filter(
            metric_type='daily',
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        for metric in metrics:
            success_rate = 0
            if metric.commands_executed + metric.commands_failed > 0:
                success_rate = (metric.commands_executed / 
                              (metric.commands_executed + metric.commands_failed)) * 100
            
            writer.writerow([
                metric.date,
                metric.user_logins,
                metric.active_users,
                metric.new_vendors,
                metric.api_tests_executed,
                metric.commands_executed,
                metric.commands_failed,
                round(success_rate, 2),
                round(metric.avg_response_time, 2),
                metric.system_errors
            ])
        
        return response
    
    def export_to_json(self, start_date, end_date):
        """Export analytics data to JSON"""
        
        metrics = DashboardMetrics.objects.filter(
            metric_type='daily',
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        data = []
        for metric in metrics:
            success_rate = 0
            if metric.commands_executed + metric.commands_failed > 0:
                success_rate = (metric.commands_executed / 
                              (metric.commands_executed + metric.commands_failed)) * 100
            
            data.append({
                'date': metric.date.isoformat(),
                'user_logins': metric.user_logins,
                'active_users': metric.active_users,
                'new_vendors': metric.new_vendors,
                'api_tests_executed': metric.api_tests_executed,
                'commands_executed': metric.commands_executed,
                'commands_failed': metric.commands_failed,
                'success_rate': round(success_rate, 2),
                'avg_response_time': round(metric.avg_response_time, 2),
                'system_errors': metric.system_errors,
                'system_warnings': metric.system_warnings
            })
        
        response = HttpResponse(
            json.dumps({
                'export_info': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'exported_at': timezone.now().isoformat(),
                    'total_records': len(data)
                },
                'data': data
            }, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="analytics_{start_date}_{end_date}.json"'
        
        return response
    
    def export_to_excel(self, start_date, end_date):
        """Export analytics data to Excel (simplified - would need openpyxl)"""
        # For simplicity, return CSV format with Excel content type
        # In production, you'd use openpyxl or xlsxwriter
        
        response = self.export_to_csv(start_date, end_date)
        response['Content-Type'] = 'application/vnd.ms-excel'
        response['Content-Disposition'] = f'attachment; filename="analytics_{start_date}_{end_date}.xls"'
        
        return response