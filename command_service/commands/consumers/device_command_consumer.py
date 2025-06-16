from shared.kafka import kafka_service
from shared.kafka.topics import Topics, EventTypes
from shared.kafka.publisher import EventPublisher
from commands.models import CommandRequest, CommandExecution
from django.utils import timezone
from django.shortcuts import get_object_or_404
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
            elif event_type == EventTypes.DEVICE_COMMAND_COMPLETED:
                self.save_command_completion(event_data, success=True)
            elif event_type == EventTypes.DEVICE_COMMAND_FAILED:
                self.save_command_completion(event_data, success=False)
            elif event_type == EventTypes.DEVICE_COMMAND_EXECUTING:
                self.update_command_executing(event_data)
                
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
            EventPublisher.publish_event(
                Topics.DEVICE_COMMANDS,
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

    def update_command_executing(self, event_data):
        """Update command status to executing when agent picks it up"""
        try:
            command_id = event_data.get('command_id')
            agent_id = event_data.get('agent_id', 'unknown')
            
            if not command_id:
                print("No command_id in executing event")
                return
                
            # Update CommandRequest status
            command_request = get_object_or_404(CommandRequest, id=command_id)
            command_request.status = 'executing'
            command_request.save()
            
            print(f"Command {command_id} is now executing by agent {agent_id}")
            
        except Exception as e:
            print(f"Error updating command executing status: {e}")
    
    def save_command_completion(self, event_data, success=True):
        """Save command completion to database"""
        try:
            command_id = event_data.get('command_id')
            device_id = event_data.get('device_id')
            command_type = event_data.get('command_type')
            agent_id = event_data.get('agent_id', 'unknown')
            execution_time = event_data.get('execution_time', 0.0)
            result = event_data.get('result', {})
            error_message = event_data.get('error', '')
            
            if not command_id:
                print("No command_id in completion event")
                return
                
            # Get CommandRequest
            try:
                command_request = CommandRequest.objects.get(id=command_id)
            except CommandRequest.DoesNotExist:
                print(f"CommandRequest {command_id} not found, creating placeholder")
                # Create placeholder if not exists (shouldn't happen normally)
                command_request = CommandRequest.objects.create(
                    id=command_id,
                    device_id=device_id or 'unknown',
                    command_type=command_type or 'unknown',
                    command_params={},
                    user_id='system',
                    status='completed' if success else 'failed'
                )
            
            # Update CommandRequest status
            command_request.status = 'completed' if success else 'failed'
            command_request.save()
            
            # Check if CommandExecution already exists (to avoid duplicates)
            existing_execution = CommandExecution.objects.filter(
                command_request=command_request
            ).first()
            
            if existing_execution:
                print(f"CommandExecution for {command_id} already exists, updating...")
                # Update existing execution
                existing_execution.result = result
                existing_execution.error_message = error_message
                existing_execution.execution_time = execution_time
                existing_execution.completed_at = timezone.now()
                existing_execution.save()
            else:
                # Create new CommandExecution record
                execution = CommandExecution.objects.create(
                    command_request=command_request,
                    agent_id=agent_id,
                    api_config_id=event_data.get('api_config_id', ''),
                    protocol=event_data.get('protocol', 'http'),
                    result=result,
                    error_message=error_message,
                    response_data=result.get('response_data', {}) if isinstance(result, dict) else {},
                    execution_time=execution_time,
                    response_size=len(str(result)) if result else 0,
                    started_at=timezone.now() - timezone.timedelta(seconds=execution_time),
                    completed_at=timezone.now()
                )
                
                print(f"Created CommandExecution {execution.id} for command {command_id}")
            
            # Log completion
            status_text = 'completed' if success else 'failed'
            print(f"Command {command_id} {status_text} in {execution_time:.2f}s by agent {agent_id}")
            
            # Optionally publish a final confirmation event for real-time updates
            EventPublisher.publish_command_event(
                EventTypes.DEVICE_COMMAND_STATUS_UPDATED,
                {
                    'command_id': command_id,
                    'status': command_request.status,
                    'execution_time': execution_time,
                    'success': success,
                    'updated_at': timezone.now().isoformat()
                }
            )
            
        except Exception as e:
            print(f"Error saving command completion: {e}")
            
    def log_command_completion(self, event_type, event_data):
        """Legacy method - now handled by save_command_completion"""
        # This method is kept for backward compatibility
        # but actual saving is done in save_command_completion
        command_id = event_data.get('command_id')
        success = event_type == EventTypes.DEVICE_COMMAND_COMPLETED
        execution_time = event_data.get('execution_time', 0)
        
        print(f"Legacy log: Command {command_id} {'completed' if success else 'failed'} in {execution_time:.2f}s")