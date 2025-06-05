from typing import Dict, Any, Optional
from .service import kafka_service, EventTypes, Topics

class EventPublisher:
    """
    Publisher cho các events của hệ thống
    """
    
    @staticmethod
    def publish_user_event(event_type: str, user_data: Dict[str, Any], 
                          additional_data: Optional[Dict[str, Any]] = None):
        """Publish user-related events"""
        data = {
            'user': user_data,
            **(additional_data or {})
        }
        
        kafka_service.send_event(
            topic=Topics.USER_EVENTS,
            event_type=event_type,
            data=data,
            key=str(user_data.get('user_id', ''))
        )
    
    @staticmethod
    def publish_vendor_event(event_type: str, vendor_data: Dict[str, Any],
                           user_id: Optional[str] = None):
        """Publish vendor-related events"""
        data = {
            'vendor': vendor_data,
            'user_id': user_id
        }
        
        kafka_service.send_event(
            topic=Topics.VENDOR_EVENTS,
            event_type=event_type,
            data=data,
            key=str(vendor_data.get('vendor_id', ''))
        )
    
    @staticmethod
    def publish_api_config_event(event_type: str, config_data: Dict[str, Any],
                                user_id: Optional[str] = None):
        """Publish API configuration events"""
        data = {
            'api_config': config_data,
            'user_id': user_id
        }
        
        kafka_service.send_event(
            topic=Topics.API_CONFIG_EVENTS,
            event_type=event_type,
            data=data,
            key=str(config_data.get('config_id', ''))
        )
    
    @staticmethod
    def publish_command_event(event_type: str, command_data: Dict[str, Any]):
        """Publish command execution events"""
        kafka_service.send_event(
            topic=Topics.COMMAND_EVENTS,
            event_type=event_type,
            data=command_data,
            key=command_data.get('device_id', command_data.get('command_id', ''))
        )
    
    @staticmethod
    def publish_audit_event(action: str, resource_type: str, resource_id: str,
                           user_id: str, changes: Optional[Dict[str, Any]] = None):
        """Publish audit events"""
        data = {
            'action': action,
            'resource_type': resource_type,
            'resource_id': resource_id,
            'user_id': user_id,
            'changes': changes or {}
        }
        
        kafka_service.send_event(
            topic=Topics.AUDIT_EVENTS,
            event_type='audit_log',
            data=data,
            key=f"{resource_type}_{resource_id}"
        )
    
    @staticmethod
    def publish_system_event(event_type: str, message: str, 
                           level: str = 'INFO', additional_data: Optional[Dict[str, Any]] = None):
        """Publish system events"""
        data = {
            'message': message,
            'level': level,
            **(additional_data or {})
        }
        
        kafka_service.send_event(
            topic=Topics.SYSTEM_EVENTS,
            event_type=event_type,
            data=data
        )
    
    @staticmethod
    def publish_event(topic: str, event_type: str, data: Dict[str, Any], 
                     key: Optional[str] = None, headers: Optional[Dict[str, str]] = None):
        """Generic event publisher"""
        kafka_service.send_event(
            topic=topic,
            event_type=event_type,
            data=data,
            key=key,
            headers=headers
        )

def publish_vendor_created(vendor_id: str, vendor_name: str, user_id: str):
    """Publish vendor created event"""
    EventPublisher.publish_vendor_event(
        EventTypes.VENDOR_CREATED,
        {'vendor_id': vendor_id, 'name': vendor_name},
        user_id
    )

def publish_command_executed(device_id: str, command_type: str, result: Dict[str, Any],
                           execution_time: float, user_id: str = None):
    """Publish command execution event"""
    EventPublisher.publish_command_event(
        EventTypes.COMMAND_EXECUTED,
        {
            'device_id': device_id,
            'command_type': command_type,
            'result': result,
            'execution_time': execution_time,
            'user_id': user_id
        }
    )

def publish_command_failed(device_id: str, command_type: str, error: str, user_id: str = None):
    """Publish command failed event"""
    EventPublisher.publish_command_event(
        EventTypes.COMMAND_FAILED,
        {
            'device_id': device_id,
            'command_type': command_type,
            'error': error,
            'user_id': user_id
        }
    )