import time
from datetime import timedelta
from django.utils import timezone
from shared.grpc.services.vendor_service import VendorServiceClient
from shared.kafka import kafka_service
from shared.kafka.topics import Topics, EventTypes
from shared.kafka.publisher import EventPublisher
from commands.protocol_handlers import get_protocol_handler
from commands.models import CommandExecution, CommandRequest

class DeviceCommandAgent:
    """Agent chuyên xử lý device commands thực tế"""
    
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.vendor_service = VendorServiceClient()
        self.is_running = False
        
    def start_consumer(self):
        """Consumer cho device commands - MUST BLOCK"""
        print(f"DeviceCommandAgent {self.agent_id} starting consumer...")
        
        try:
            # Check Kafka service
            if not kafka_service.kafka_enabled:
                raise Exception("Kafka service not enabled")
            
            # Create consumer - listen for EXECUTING events
            success = kafka_service.create_consumer(
                topics=[Topics.DEVICE_COMMANDS],
                group_id=f'device-command-agents-{self.agent_id}',
                message_handler=self.handle_device_command
            )
            
            if not success:
                raise Exception("Failed to create Kafka consumer")
            
            print(f"DeviceCommandAgent {self.agent_id} consumer created successfully")
            
            # CRITICAL: Keep running to block the thread
            self.is_running = True
            while self.is_running:
                time.sleep(1)
                
        except Exception as e:
            print(f"DeviceCommandAgent {self.agent_id} error: {e}")
            raise
    
    def stop(self):
        """Stop the agent gracefully"""
        print(f"Stopping DeviceCommandAgent {self.agent_id}")
        self.is_running = False
        kafka_service.stop_consumer(f'device-command-agents-{self.agent_id}')
    
    def handle_device_command(self, message):
        """Handle device command execution"""
        try:
            event_type = message.get('event_type')
            command_data = message.get('data', {})
            
            # Only process EXECUTING events (từ command consumer)
            if event_type == EventTypes.DEVICE_COMMAND_EXECUTING:
                print(f"DeviceCommandAgent {self.agent_id} processing command: {command_data.get('command_id')}")
                self.execute_device_command(command_data)
                
        except Exception as e:
            print(f"DeviceCommandAgent {self.agent_id} error handling command: {e}")
            
    def execute_device_command(self, command_data):
        """Execute command on actual device"""
        command_id = command_data.get('command_id')
        
        try:
            device_id = command_data.get('device_id')
            command_type = command_data.get('command_type')
            command_params = command_data.get('command_params', {})
            
            print(f"Executing device command {command_type} on device {device_id}")
            
            # Get and update CommandRequest status
            try:
                command_request = CommandRequest.objects.get(id=command_id)
                command_request.status = 'executing'
                command_request.save()
            except CommandRequest.DoesNotExist:
                print(f"Warning: CommandRequest {command_id} not found, creating new one")
                command_request = CommandRequest.objects.create(
                    id=command_id,
                    device_id=device_id,
                    command_type=command_type,
                    command_params=command_params,
                    user_id=command_data.get('user_id', 'system'),
                    status='executing'
                )
            
            # Lấy full context từ gRPC
            context = self.get_device_command_context(device_id, command_type)
            
            # Execute với device-specific context
            start_time = time.time()
            handler = get_protocol_handler("http")
            result = handler.execute_command(
                context.api_config,
                context.command,
                command_params,
                device=context.device
            )
            execution_time = time.time() - start_time
            
            success = result.get('success', False)
            print(f"Device command completed in {execution_time:.2f}s: {success}")
            
            # Update CommandRequest status
            command_request.status = 'completed' if success else 'failed'
            command_request.save()
            
            # Store execution record với correct ForeignKey
            CommandExecution.objects.create(
                command_request=command_request,  # Sử dụng ForeignKey thay vì command_request_id
                agent_id=self.agent_id,
                api_config_id=str(context.api_config.id),
                protocol="http",
                result=result,
                error_message=result.get('error', '') if not success else '',
                response_data=result.get('response_data', {}),
                execution_time=execution_time,
                response_size=len(str(result.get('response_data', {}))),
                started_at=timezone.now() - timedelta(seconds=execution_time),
                completed_at=timezone.now()
            )
            
            # Publish success/failure event
            event_type = EventTypes.DEVICE_COMMAND_COMPLETED if success else EventTypes.DEVICE_COMMAND_FAILED
            EventPublisher.publish_command_event(
                event_type,
                {
                    'command_id': command_id,
                    'device_id': device_id,
                    'command_type': command_type,
                    'result': result,
                    'execution_time': execution_time,
                    'agent_id': self.agent_id,
                    'success': success,
                    'status': command_request.status
                }
            )
            
        except Exception as e:
            print(f"DeviceCommandAgent {self.agent_id} execute_device_command error: {e}")
            
            # Update CommandRequest status to failed
            try:
                if command_id:
                    command_request = CommandRequest.objects.get(id=command_id)
                    command_request.status = 'failed'
                    command_request.save()
                    
                    # Store failed execution record
                    CommandExecution.objects.create(
                        command_request=command_request,
                        agent_id=self.agent_id,
                        api_config_id='',
                        protocol="http",
                        result={},
                        error_message=str(e),
                        response_data={},
                        execution_time=0,
                        response_size=0,
                        started_at=timezone.now(),
                        completed_at=timezone.now()
                    )
            except Exception as update_error:
                print(f"Failed to update command status: {update_error}")
            
            # Publish failure event
            EventPublisher.publish_command_event(
                EventTypes.DEVICE_COMMAND_FAILED,
                {
                    'command_id': command_id,
                    'device_id': command_data.get('device_id'),
                    'command_type': command_data.get('command_type'),
                    'error': str(e),
                    'agent_id': self.agent_id,
                    'success': False,
                    'status': 'failed'
                }
            )
    
    def get_device_command_context(self, device_id, command_type):
        """Get full device command context via gRPC"""
        try:
            return self.vendor_service.get_command_context(device_id=device_id, command_type=command_type)
        except Exception as e:
            raise ValueError(f"Failed to get device command context for {device_id}: {e}")