import functools
import inspect
import time
from typing import Dict, Any, Callable, Optional
from .publisher import EventPublisher
from .topics import Topics, EventTypes

def kafka_event(topic: str, event_type: str, 
                data_extractor: Optional[Callable] = None,
                key_extractor: Optional[Callable] = None):
    """
    Decorator để tự động publish event sau khi method thực thi thành công
    
    Args:
        topic: Kafka topic name
        event_type: Event type
        data_extractor: Function để extract data từ method args/kwargs/result
        key_extractor: Function để extract message key
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                # Execute original method
                result = func(*args, **kwargs)
                
                # Extract data for event
                if data_extractor:
                    event_data = data_extractor(args, kwargs, result)
                else:
                    event_data = _default_data_extractor(func, args, kwargs, result)
                
                # Extract key
                message_key = None
                if key_extractor:
                    message_key = key_extractor(args, kwargs, result)
                
                # Publish event
                EventPublisher.publish_event(
                    topic=topic,
                    event_type=event_type,
                    data=event_data,
                    key=message_key
                )
                
                return result
                
            except Exception as e:
                # If original method fails, publish error event if needed
                if event_type.endswith('_failed'):
                    error_data = {
                        'error': str(e),
                        'method': func.__name__,
                        'args': str(args),
                        'kwargs': str(kwargs)
                    }
                    EventPublisher.publish_event(
                        topic=Topics.SYSTEM_EVENTS,
                        event_type=EventTypes.SYSTEM_ERROR,
                        data=error_data
                    )
                raise
        
        return wrapper
    return decorator

def kafka_audit(resource_type: str, action: str = None,
                resource_id_extractor: Optional[Callable] = None):
    """
    Decorator để tự động tạo audit log
    
    Args:
        resource_type: Loại resource (vendor, api_config, user, etc.)
        action: Action type (create, update, delete, etc.)
        resource_id_extractor: Function để extract resource ID
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get user from request (assuming Django view)
            request = None
            user_id = None
            
            # Try to extract request from args
            for arg in args:
                if hasattr(arg, 'user') and hasattr(arg, 'META'):
                    request = arg
                    if hasattr(request.user, 'id'):
                        user_id = str(request.user.id)
                    break
            
            # Execute original method
            result = func(*args, **kwargs)
            
            # Extract resource ID
            resource_id = None
            if resource_id_extractor:
                resource_id = resource_id_extractor(args, kwargs, result)
            elif hasattr(result, 'data') and isinstance(result.data, dict):
                resource_id = result.data.get('id')
            
            # Determine action from method name if not provided
            if not action:
                method_name = func.__name__.lower()
                if 'create' in method_name:
                    audit_action = 'create'
                elif 'update' in method_name or 'patch' in method_name:
                    audit_action = 'update'
                elif 'delete' in method_name or 'destroy' in method_name:
                    audit_action = 'delete'
                else:
                    audit_action = method_name
            else:
                audit_action = action
            
            # Publish audit event
            if user_id and resource_id:
                EventPublisher.publish_audit_event(
                    action=audit_action,
                    resource_type=resource_type,
                    resource_id=str(resource_id),
                    user_id=user_id,
                    changes=_extract_changes(args, kwargs, result)
                )
            
            return result
        
        return wrapper
    return decorator

def kafka_command_tracking(device_id_extractor: Callable = None):
    """
    Decorator để track command execution
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            # Extract device ID
            device_id = None
            if device_id_extractor:
                device_id = device_id_extractor(args, kwargs)
            
            # Track command start
            start_time = time.time()
            command_type = kwargs.get('command_type', func.__name__)
            
            EventPublisher.publish_command_event(
                EventTypes.COMMAND_EXECUTING,
                {
                    'device_id': device_id,
                    'command_type': command_type,
                    'start_time': start_time
                }
            )
            
            try:
                # Execute command
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Track success
                EventPublisher.publish_command_event(
                    EventTypes.COMMAND_EXECUTED,
                    {
                        'device_id': device_id,
                        'command_type': command_type,
                        'result': result,
                        'execution_time': execution_time
                    }
                )
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Track failure
                EventPublisher.publish_command_event(
                    EventTypes.COMMAND_FAILED,
                    {
                        'device_id': device_id,
                        'command_type': command_type,
                        'error': str(e),
                        'execution_time': execution_time
                    }
                )
                
                raise
        
        return wrapper
    return decorator

# Helper functions
def _default_data_extractor(func, args, kwargs, result):
    """Default data extractor"""
    data = {
        'method': func.__name__,
        'module': func.__module__,
    }
    
    # Try to extract meaningful data from result
    if hasattr(result, 'data'):
        data['result'] = result.data
    elif isinstance(result, dict):
        data['result'] = result
    
    return data

def _extract_changes(args, kwargs, result):
    """Extract changes for audit log"""
    changes = {}
    
    # Try to extract old/new values from kwargs
    if 'instance' in kwargs and hasattr(kwargs['instance'], '__dict__'):
        # This might be an update operation
        old_values = {}
        for key, value in kwargs['instance'].__dict__.items():
            if not key.startswith('_'):
                old_values[key] = str(value)
        changes['old'] = old_values
    
    # Extract new values from result
    if hasattr(result, 'data') and isinstance(result.data, dict):
        changes['new'] = result.data
    
    return changes

# Convenience decorators for common use cases
def track_user_action(action: str):
    """Track user actions"""
    return kafka_audit('user', action)

def track_vendor_action(action: str):
    """Track vendor actions"""
    return kafka_audit('vendor', action)

def track_api_config_action(action: str):
    """Track API config actions"""
    return kafka_audit('api_config', action)