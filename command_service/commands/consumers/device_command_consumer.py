from shared.kafka import kafka_service
from shared.kafka.topics import Topics, EventTypes
from shared.kafka.publisher import EventPublisher
from commands.models import CommandRequest
from django.utils import timezone
import uuid

class DeviceCommandConsumer:
    """Consumer to handle device command requests from vendor service"""
    
    def __init__(self):
        self.setup_consumer()
    
    def setup_consumer(self):
        """Setup Kafka consumer for device command requests"""
        try:
            kafka_service.create_consumer(
                topics=[Topics.DEVICE_COMMANDS],
                group_id='command-service-device-commands',
                message_handler=self.handle_device_command_event
            )
            print("DeviceCommandConsumer initialized successfully")
        except Exception as e:
            print(f"Failed to setup DeviceCommandConsumer: {e}")
    
    def handle_device_command_event(self, message):
        """Handle all device command events"""
        try:
            event_type = message.get('event_type')
            event_data = message.get('data', {})
            
            # Route to appropriate handler
            if event_type == EventTypes.DEVICE_COMMAND_REQUESTED:
                self.process_command_request(event_data)
            elif event_type in [EventTypes.DEVICE_COMMAND_COMPLETED, EventTypes.DEVICE_COMMAND_FAILED]:
                # Log completion events for monitoring
                self.log_command_completion(event_type, event_data)
                
        except Exception as e:
            print(f"Error processing device command event: {e}")
    
    def process_command_request(self, command_data):
        """Process and queue device command for execution"""
        try:
            # Extract command data
            command_id = command_data.get('command_id')
            device_id = command_data.get('device_id')
            command_type = command_data.get('command_type')
            command_params = command_data.get('command_params', {})
            user_id = command_data.get('user_id', 'system')
            
            # Validate required fields
            if not all([command_id, device_id, command_type]):
                raise ValueError("Missing required fields: command_id, device_id, command_type")
            
            # Create CommandRequest record if not exists
            command_request, created = CommandRequest.objects.get_or_create(
                id=command_id,
                defaults={
                    'device_id': device_id,
                    'command_type': command_type,
                    'command_params': command_params,
                    'user_id': user_id,
                    'status': 'queued'
                }
            )
            
            if created:
                print(f"Created command request {command_id} for device {device_id}")
            else:
                print(f"Command request {command_id} already exists, updating status to queued")
                command_request.status = 'queued'
                command_request.save()
            
            # Publish to execution queue for agents to pick up
            EventPublisher.publish_command_event(
                EventTypes.DEVICE_COMMAND_EXECUTING,
                {
                    'command_id': str(command_request.id),
                    'device_id': device_id,
                    'command_type': command_type,
                    'command_params': command_params,
                    'user_id': user_id,
                    'created_at': command_request.created_at.isoformat()
                }
            )
            
            print(f"Queued command {command_id} for execution")
            
        except Exception as e:
            print(f"Error processing command request: {e}")
            
            # Publish failure event if possible
            if command_data.get('command_id'):
                EventPublisher.publish_command_event(
                    EventTypes.DEVICE_COMMAND_FAILED,
                    {
                        'command_id': command_data.get('command_id'),
                        'device_id': command_data.get('device_id'),
                        'command_type': command_data.get('command_type'),
                        'error': f'Failed to queue command: {str(e)}',
                        'stage': 'queuing'
                    }
                )
    
    def log_command_completion(self, event_type, event_data):
        """Log command completion for monitoring"""
        command_id = event_data.get('command_id')
        success = event_type == EventTypes.DEVICE_COMMAND_COMPLETED
        execution_time = event_data.get('execution_time', 0)
        
        print(f"Command {command_id} {'completed' if success else 'failed'} in {execution_time:.2f}s")