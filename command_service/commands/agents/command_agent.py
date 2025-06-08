import time
from datetime import timedelta
from django.utils import timezone
from shared.grpc.services.vendor_service import VendorServiceClient
from shared.kafka import kafka_service
from shared.kafka.topics import Topics, EventTypes
from shared.kafka.publisher import EventPublisher
from commands.protocol_handlers import get_protocol_handler
from commands.models import CommandExecution, CommandRequest

class CommandAgent:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.is_running = False
        self.current_command = None
        
    def start(self):
        """Start command processing agents"""
        self.start_consumer()
    
    def start_consumer(self):
        """Consumer for normal priority commands"""
        kafka_service.create_consumer(
            topics=[Topics.COMMAND_REQUESTS],
            group_id=f'command-agents-normal-{self.agent_id}',
            message_handler=self.handle_command
        )
    
    def handle_command(self, message):
        """Handle normal priority commands"""
        try:
            command_data = message.get('data', {})
            self.execute_command(command_data, priority=False)
        except Exception as e:
            print(f"Error handling normal command: {e}")
            # self.publish_command_failure(command_data, str(e))
    
    def execute_command(self, command_data, priority=False):
        """Execute single command"""
        command_type = command_data.get('command_type')
        api_config_id = command_data.get('api_config_id')
        
        try:
            EventPublisher.publish_command_event(
                EventTypes.COMMAND_EXECUTING,
                {
                    'command_id': command_data.get('command_id'),
                    'command_type': command_type,
                    'agent_id': self.agent_id,
                    'priority': priority
                }
            )
            # Get API configuration from vendor service
            api_config = self.get_api_config(api_config_id=api_config_id)
            # Get command template
            command_template = self.get_command_template(
                api_config, 
                command_data.get('command_type')
            )
            
            # Execute via protocol handler
            start_time = time.time()
            handler = get_protocol_handler("http")
            result = handler.execute_command(
                api_config, 
                command_template, 
                command_data.get('command_params', {})
            )
            execution_time = time.time() - start_time
            
            # Store execution record
            CommandExecution.objects.create(
                agent_id=self.agent_id,
                api_config_id=str(api_config.get('id')),
                protocol="http",
                result=result,
                execution_time=execution_time,
                started_at=timezone.now() - timedelta(seconds=execution_time),
                completed_at=timezone.now()
            )
            
            # Publish analytics event
            EventPublisher.publish_command_event(
                EventTypes.COMMAND_EXECUTED,
                {
                    'command_id': command_data.get('command_id'),
                    'command_type': command_data.get('command_type'),
                    'result': result,
                    'execution_time': execution_time,
                    'agent_id': self.agent_id,
                    'priority': priority
                }
            )
            print(f"Command {command_data.get('command_id')} executed successfully in {execution_time:.2f} seconds")
            
        except Exception as e:
            print(f"Error executing command {command_data.get('command_id')}: {e}")
            # self.handle_command_failure(command_data, e)
            
    def get_command_template(self, api_config, command_type):
        """Get command template for the given API config and command type"""
        client = VendorServiceClient()
        return client.get_command_template(api_config.id, command_type)
    
    def get_api_config(self, device_id=None, api_config_id=None):
        """Get API config from vendor service"""
        client = VendorServiceClient()
        if api_config_id:
            return client.get_api_config_by_id(api_config_id)
        else:
            raise ValueError("Either device_id or api_config_id must be provided")