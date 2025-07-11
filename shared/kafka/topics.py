class Topics:
    """Kafka topic names"""
    USER_EVENTS = 'user-events'
    VENDOR_EVENTS = 'vendor-events'
    API_CONFIG_EVENTS = 'api-config-events'
    COMMAND_EVENTS = 'command-events'
    SYSTEM_EVENTS = 'system-events'
    AUDIT_EVENTS = 'audit-events'
    METRICS_EVENTS = 'metrics-events'
    
    API_TEST_REQUESTS = 'api-test-requests'
    DEVICE_COMMANDS = 'device-commands'
    DEVICE_STATUS = 'device-status'
    COMMAND_RESULTS = 'command-results'

class EventTypes:
    """Event type constants"""
    
    # User events
    USER_LOGIN = 'user_login'
    USER_LOGOUT = 'user_logout'
    USER_REGISTERED = 'user_registered'
    USER_UPDATED = 'user_updated'
    USER_ACTIVATED = 'user_activated'
    USER_DEACTIVATED = 'user_deactivated'
    
    # Vendor events
    VENDOR_CREATED = 'vendor_created'
    VENDOR_UPDATED = 'vendor_updated'
    VENDOR_ACTIVATED = 'vendor_activated'
    VENDOR_DEACTIVATED = 'vendor_deactivated'
    
    # API Configuration events
    API_CONFIG_CREATED = 'api_config_created'
    API_CONFIG_UPDATED = 'api_config_updated'
    API_CONFIG_TESTED = 'api_config_tested'
    API_CONFIG_ACTIVATED = 'api_config_activated'
    API_CONFIG_DEACTIVATED = 'api_config_deactivated'
    API_CONFIG_DELETED = 'api_config_deleted'
    
    # API Test events
    API_TEST_REQUESTED = 'api_test_requested'
    API_TEST_EXECUTING = 'api_test_executing'
    API_TEST_COMPLETED = 'api_test_completed'
    API_TEST_FAILED = 'api_test_failed'
    
    # Command execution events (GENERAL)
    COMMAND_REQUESTED = 'command_requested'
    COMMAND_EXECUTING = 'command_executing'
    COMMAND_EXECUTED = 'command_executed'
    COMMAND_FAILED = 'command_failed'
    COMMAND_TIMEOUT = 'command_timeout'
    
    # Device Command events
    DEVICE_COMMAND_REQUESTED = 'device_command_requested'
    DEVICE_COMMAND_EXECUTING = 'device_command_executing'
    DEVICE_COMMAND_COMPLETED = 'device_command_completed'
    DEVICE_COMMAND_FAILED = 'device_command_failed'
    DEVICE_COMMAND_TIMEOUT = 'device_command_timeout'
    
    # Command Template events
    COMMAND_TEMPLATE_DELETED = 'command_template_deleted'
    COMMAND_TEMPLATE_TYPE_CHANGED = 'command_template_type_changed'
    
    # Device events
    DEVICE_ONLINE = 'device_online'
    DEVICE_OFFLINE = 'device_offline'
    DEVICE_STATUS_CHANGED = 'device_status_changed'
    DEVICE_COMMANDS_DISCONNECTED = 'device_commands_disconnected'
    
    # Command Result events
    COMMAND_RESULT_SUCCESS = 'command_result_success'
    COMMAND_RESULT_ERROR = 'command_result_error'
    
    # System events
    SYSTEM_ERROR = 'system_error'
    SYSTEM_WARNING = 'system_warning'
    SYSTEM_INFO = 'system_info'
    SERVICE_STARTED = 'service_started'
    SERVICE_STOPPED = 'service_stopped'
    HEALTH_CHECK = 'health_check'
    
    # Audit events
    AUDIT_LOG = 'audit_log'
    SECURITY_EVENT = 'security_event'
    ACCESS_GRANTED = 'access_granted'
    ACCESS_DENIED = 'access_denied'

class EventSeverity:
    """Event severity levels"""
    DEBUG = 'debug'
    INFO = 'info'
    WARNING = 'warning'
    ERROR = 'error'
    CRITICAL = 'critical'

# Topic configuration for auto-creation
TOPIC_CONFIGS = {
    Topics.USER_EVENTS: {
        'partitions': 3,
        'replication_factor': 1,
        'config': {
            'retention.ms': str(30 * 24 * 60 * 60 * 1000),  # 30 days
            'cleanup.policy': 'delete',
            'compression.type': 'snappy'
        }
    },
    Topics.VENDOR_EVENTS: {
        'partitions': 3,
        'replication_factor': 1,
        'config': {
            'retention.ms': str(30 * 24 * 60 * 60 * 1000),  # 30 days
            'cleanup.policy': 'delete',
            'compression.type': 'snappy'
        }
    },
    Topics.API_CONFIG_EVENTS: {
        'partitions': 3,
        'replication_factor': 1,
        'config': {
            'retention.ms': str(30 * 24 * 60 * 60 * 1000),  # 30 days
            'cleanup.policy': 'delete',
            'compression.type': 'snappy'
        }
    },
    Topics.COMMAND_EVENTS: {
        'partitions': 3,
        'replication_factor': 1,
        'config': {
            'retention.ms': str(7 * 24 * 60 * 60 * 1000),  # 7 days
            'cleanup.policy': 'delete',
            'compression.type': 'snappy'
        }
    },
    Topics.SYSTEM_EVENTS: {
        'partitions': 3,
        'replication_factor': 1,
        'config': {
            'retention.ms': str(7 * 24 * 60 * 60 * 1000),  # 7 days
            'cleanup.policy': 'delete',
            'compression.type': 'snappy'
        }
    },
    Topics.AUDIT_EVENTS: {
        'partitions': 3,
        'replication_factor': 1,
        'config': {
            'retention.ms': str(365 * 24 * 60 * 60 * 1000),  # 1 year
            'cleanup.policy': 'delete',
            'compression.type': 'snappy'
        }
    },
    Topics.METRICS_EVENTS: {
        'partitions': 6,
        'replication_factor': 1,
        'config': {
            'retention.ms': str(7 * 24 * 60 * 60 * 1000),  # 7 days
            'cleanup.policy': 'delete',
            'compression.type': 'snappy'
        }
    },
    
    # NEW TOPICS
    Topics.API_TEST_REQUESTS: {
        'partitions': 3,
        'replication_factor': 1,
        'config': {
            'retention.ms': str(24 * 60 * 60 * 1000),  # 24 hours
            'cleanup.policy': 'delete',
            'compression.type': 'snappy'
        }
    },
    Topics.DEVICE_COMMANDS: {
        'partitions': 3,
        'replication_factor': 1,
        'config': {
            'retention.ms': str(7 * 24 * 60 * 60 * 1000),  # 7 days
            'cleanup.policy': 'delete',
            'compression.type': 'snappy',
            'max.message.bytes': '10485760'
        }
    },
    Topics.DEVICE_STATUS: {
        'partitions': 6,
        'replication_factor': 1,
        'config': {
            'retention.ms': str(3 * 24 * 60 * 60 * 1000),  # 3 days
            'cleanup.policy': 'delete',
            'compression.type': 'snappy'
        }
    },
    Topics.COMMAND_RESULTS: {
        'partitions': 6,
        'replication_factor': 1,
        'config': {
            'retention.ms': str(7 * 24 * 60 * 60 * 1000),  # 7 days
            'cleanup.policy': 'delete',
            'compression.type': 'snappy'
        }
    },
}