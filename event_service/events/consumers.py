import json
import logging
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from shared.kafka.service import kafka_service, Topics
from .models import EventLog, AuditLog, CommandExecutionLog, SystemMetrics  # Local models

logger = logging.getLogger(__name__)

class EventServiceConsumers:
    """
    Consumers chỉ chạy trong event service
    Import models từ local events app
    """
    
    @staticmethod
    def start_all_consumers():
        """Start tất cả consumers cho event service"""
        
        kafka_service.create_consumer(
            topics=[Topics.USER_EVENTS],
            group_id='event-service-user-processor',
            message_handler=EventServiceConsumers.handle_user_event
        )
        
        kafka_service.create_consumer(
            topics=[Topics.VENDOR_EVENTS],
            group_id='event-service-vendor-processor', 
            message_handler=EventServiceConsumers.handle_vendor_event
        )
        
        kafka_service.create_consumer(
            topics=[Topics.API_CONFIG_EVENTS],
            group_id='event-service-config-processor',
            message_handler=EventServiceConsumers.handle_api_config_event
        )
        
        kafka_service.create_consumer(
            topics=[Topics.COMMAND_EVENTS],
            group_id='event-service-command-processor',
            message_handler=EventServiceConsumers.handle_command_event
        )
        
        kafka_service.create_consumer(
            topics=[Topics.SYSTEM_EVENTS],
            group_id='event-service-system-processor',
            message_handler=EventServiceConsumers.handle_system_event
        )
        
        kafka_service.create_consumer(
            topics=[Topics.AUDIT_EVENTS],
            group_id='event-service-audit-processor',
            message_handler=EventServiceConsumers.handle_audit_event
        )
        
        logger.info("Event Service: All Kafka consumers started")
    
    @staticmethod
    def handle_user_event(message):
        """Handle user events và lưu vào local EventLog model"""
        try:
            event_id = message.get('event_id')
            event_type = message.get('event_type')
            data = message.get('data', {})
            timestamp = parse_datetime(message.get('timestamp')) or timezone.now()
            source_service = message.get('source_service')
            
            # Lưu vào local EventLog model
            EventLog.objects.create(
                event_id=event_id,
                category='user',
                event_type=event_type,
                severity='info',
                data=data,
                source_service=source_service,
                user_id=data.get('user', {}).get('user_id'),
                event_timestamp=timestamp
            )
            
            # Tạo metrics
            if event_type == 'user_login':
                SystemMetrics.objects.create(
                    metric_type='user_activity',
                    metric_name='login_count',
                    value=1,
                    unit='count',
                    source_service=source_service,
                    tags={'user_id': data.get('user', {}).get('user_id')}
                )
            
            logger.info(f"Processed user event: {event_type}")
            
        except Exception as e:
            logger.error(f"Error processing user event: {e}")
    
    @staticmethod
    def handle_vendor_event(message):
        """Handle vendor events"""
        try:
            event_id = message.get('event_id')
            event_type = message.get('event_type')
            data = message.get('data', {})
            timestamp = parse_datetime(message.get('timestamp')) or timezone.now()
            source_service = message.get('source_service')
            
            # Lưu vào EventLog
            EventLog.objects.create(
                event_id=event_id,
                category='vendor',
                event_type=event_type,
                severity='info',
                data=data,
                source_service=source_service,
                user_id=data.get('user_id'),
                event_timestamp=timestamp
            )
            
            # Tạo audit log cho vendor actions
            if event_type in ['vendor_created', 'vendor_updated', 'vendor_activated', 'vendor_deactivated']:
                EventServiceConsumers._create_vendor_audit_log(event_type, data, timestamp)
            
            logger.info(f"Processed vendor event: {event_type}")
            
        except Exception as e:
            logger.error(f"Error processing vendor event: {e}")
    
    @staticmethod
    def handle_command_event(message):
        """Handle command execution events"""
        try:
            event_id = message.get('event_id')
            event_type = message.get('event_type')
            data = message.get('data', {})
            timestamp = parse_datetime(message.get('timestamp')) or timezone.now()
            source_service = message.get('source_service')
            
            # Lưu vào EventLog
            severity = 'error' if event_type == 'command_failed' else 'info'
            EventLog.objects.create(
                event_id=event_id,
                category='command',
                event_type=event_type,
                severity=severity,
                data=data,
                source_service=source_service,
                user_id=data.get('user_id'),
                event_timestamp=timestamp
            )
            
            # Lưu detailed command log
            EventServiceConsumers._store_command_execution(event_type, data, timestamp)
            
            # Tạo metrics
            EventServiceConsumers._create_command_metrics(event_type, data)
            
            logger.info(f"Processed command event: {event_type}")
            
        except Exception as e:
            logger.error(f"Error processing command event: {e}")
    
    @staticmethod
    def handle_system_event(message):
        """Handle system events"""
        try:
            event_id = message.get('event_id')
            event_type = message.get('event_type')
            data = message.get('data', {})
            timestamp = parse_datetime(message.get('timestamp')) or timezone.now()
            source_service = message.get('source_service')
            severity = data.get('level', 'info').lower()
            
            # Lưu vào EventLog
            EventLog.objects.create(
                event_id=event_id,
                category='system',
                event_type=event_type,
                severity=severity,
                data=data,
                source_service=source_service,
                event_timestamp=timestamp
            )
            
            logger.info(f"Processed system event: {event_type}")
            
        except Exception as e:
            logger.error(f"Error processing system event: {e}")
    
    @staticmethod
    def handle_audit_event(message):
        """Handle audit events"""
        try:
            data = message.get('data', {})
            timestamp = parse_datetime(message.get('timestamp')) or timezone.now()
            
            # Lưu vào local AuditLog model
            AuditLog.objects.create(
                action=data.get('action'),
                resource_type=data.get('resource_type'),
                resource_id=data.get('resource_id'),
                user_id=data.get('user_id'),
                username=data.get('username', ''),
                organization_id=data.get('organization_id'),
                old_values=data.get('changes', {}).get('old', {}),
                new_values=data.get('changes', {}).get('new', {}),
                ip_address=data.get('ip_address'),
                user_agent=data.get('user_agent', ''),
                timestamp=timestamp
            )
            
            logger.info(f"Processed audit event: {data.get('action')}")
            
        except Exception as e:
            logger.error(f"Error processing audit event: {e}")
    
    # Helper methods
    @staticmethod
    def _create_vendor_audit_log(event_type, data, timestamp):
        """Tạo audit log từ vendor events"""
        vendor_data = data.get('vendor', {})
        
        action_map = {
            'vendor_created': 'create',
            'vendor_updated': 'update', 
            'vendor_activated': 'activate',
            'vendor_deactivated': 'deactivate'
        }
        
        action = action_map.get(event_type, 'update')
        
        AuditLog.objects.create(
            action=action,
            resource_type='vendor',
            resource_id=vendor_data.get('vendor_id', ''),
            user_id=data.get('user_id', ''),
            old_values=data.get('old_data', {}),
            new_values=data.get('new_data', vendor_data),
            timestamp=timestamp
        )
    
    @staticmethod
    def _store_command_execution(event_type, data, timestamp):
        """Lưu command execution details"""
        try:
            device_id = data.get('device_id')
            command_type = data.get('command_type')
            
            if event_type == 'command_executed':
                CommandExecutionLog.objects.update_or_create(
                    device_id=device_id,
                    command_type=command_type,
                    status='pending',
                    defaults={
                        'status': 'success',
                        'result': data.get('result', {}),
                        'execution_time': data.get('execution_time'),
                        'completed_at': timestamp,
                        'user_id': data.get('user_id'),
                        'test_mode': data.get('test_mode', False)
                    }
                )
            elif event_type == 'command_failed':
                CommandExecutionLog.objects.update_or_create(
                    device_id=device_id,
                    command_type=command_type,
                    status='pending',
                    defaults={
                        'status': 'failed',
                        'error_message': data.get('error', ''),
                        'execution_time': data.get('execution_time'),
                        'completed_at': timestamp,
                        'user_id': data.get('user_id'),
                        'test_mode': data.get('test_mode', False)
                    }
                )
                
        except Exception as e:
            logger.error(f"Error storing command execution: {e}")
    
    @staticmethod
    def _create_command_metrics(event_type, data):
        """Tạo command metrics"""
        try:
            if event_type == 'command_executed':
                # Success metric
                SystemMetrics.objects.create(
                    metric_type='command_success_rate',
                    metric_name='command_success',
                    value=1,
                    unit='count',
                    source_service='vendor-service',
                    tags={'device_id': data.get('device_id')}
                )
                
                # Response time metric
                execution_time = data.get('execution_time', 0)
                if execution_time > 0:
                    SystemMetrics.objects.create(
                        metric_type='api_response_time',
                        metric_name='command_execution_time',
                        value=execution_time,
                        unit='seconds',
                        source_service='vendor-service',
                        tags={'device_id': data.get('device_id')}
                    )
                    
            elif event_type == 'command_failed':
                # Failure metric
                SystemMetrics.objects.create(
                    metric_type='error_rate',
                    metric_name='command_failure',
                    value=1,
                    unit='count',
                    source_service='vendor-service',
                    tags={'device_id': data.get('device_id')}
                )
                
        except Exception as e:
            logger.error(f"Error creating command metrics: {e}")

# Consumer manager
class EventConsumerManager:
    @staticmethod
    def start_consumers():
        """Start consumers cho event service"""
        try:
            EventServiceConsumers.start_all_consumers()
            logger.info("Event Service consumers started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start Event Service consumers: {e}")
            return False