import time
from datetime import timedelta
from django.utils import timezone
from shared.grpc.services.vendor_service import VendorServiceClient
from shared.kafka import kafka_service
from shared.kafka.topics import Topics, EventTypes
from shared.kafka.publisher import EventPublisher
from commands.protocol_handlers import get_protocol_handler
from commands.models import CommandExecution, CommandRequest

class APITestAgent:
    """Agent chuyên xử lý test API configuration"""
    
    def __init__(self, agent_id):
        self.agent_id = agent_id  # Đã có "test-" prefix từ management command
        self.vendor_service = VendorServiceClient()
        self.is_running = False
        
    def start_consumer(self):
        """Consumer cho API test requests - MUST BLOCK"""
        print(f"APITestAgent {self.agent_id} starting consumer...")
        
        try:
            # Check Kafka service
            if not kafka_service.kafka_enabled:
                raise Exception("Kafka service not enabled")
            
            # Create consumer
            success = kafka_service.create_consumer(
                topics=[Topics.API_TEST_REQUESTS],
                group_id=f'api-test-agents-{self.agent_id}',
                message_handler=self.handle_test_command
            )
            
            if not success:
                raise Exception("Failed to create Kafka consumer")
            
            print(f"APITestAgent {self.agent_id} consumer created successfully")
            
            # CRITICAL: Keep running to block the thread
            self.is_running = True
            while self.is_running:
                time.sleep(1)
                # Optional: Add heartbeat or health check here
                
        except Exception as e:
            print(f"APITestAgent {self.agent_id} error: {e}")
            raise
    
    def stop(self):
        """Stop the agent gracefully"""
        print(f"Stopping APITestAgent {self.agent_id}")
        self.is_running = False
        kafka_service.stop_consumer(f'api-test-agents-{self.agent_id}')
    
    def handle_test_command(self, message):
        """Handle API configuration test"""
        try:
            test_data = message.get('data', {})
            print(f"APITestAgent {self.agent_id} processing test: {test_data.get('test_id')}")
            self.execute_api_test(test_data)
        except Exception as e:
            print(f"APITestAgent {self.agent_id} error handling test: {e}")
            
    def execute_api_test(self, test_data):
        """Test API configuration without device context"""
        try:
            api_config_id = test_data.get('api_config_id')
            command_id = test_data.get('command_id')
            test_params = test_data.get('params', {})
            
            print(f"Testing API config {api_config_id} with command {command_id}")
            
            # Lấy API config + command template
            api_config = self.get_api_config(api_config_id=api_config_id)
            command_template = self.get_command_template(command_id)
            
            # Execute test
            start_time = time.time()
            handler = get_protocol_handler("http")
            result = handler.execute_command(
                api_config, 
                command_template, 
                test_params,
                device=None
            )
            execution_time = time.time() - start_time
            
            print(f"Test completed in {execution_time:.2f}s: {result.get('success', False)}")
            
            # Publish test result
            EventPublisher.publish_event(
                Topics.API_CONFIG_EVENTS,
                EventTypes.API_CONFIG_TESTED,
                {
                    'test_id': test_data.get('test_id'),
                    'api_config_id': api_config_id,
                    'command_id': command_id,
                    'result': result,
                    'execution_time': execution_time,
                    'agent_id': self.agent_id,
                    'success': result.get('success', False)
                }
            )
            
        except Exception as e:
            print(f"APITestAgent {self.agent_id} execute_api_test error: {e}")
            
            # Publish test failure
            EventPublisher.publish_event(
                Topics.API_CONFIG_EVENTS,
                EventTypes.API_CONFIG_TESTED,
                {
                    'test_id': test_data.get('test_id'),
                    'api_config_id': test_data.get('api_config_id'),
                    'command_id': test_data.get('command_id'),
                    'result': {'success': False, 'error': str(e)},
                    'agent_id': self.agent_id,
                    'success': False
                }
            )
        
    def get_api_config(self, api_config_id):
        """Lấy API configuration từ vendor service"""
        try:
            response = self.vendor_service.get_api_config_by_id(api_config_id)
            return response
        except Exception as e:
            raise ValueError(f"Failed to get API configuration {api_config_id}: {e}")
    
    def get_command_template(self, command_id):
        """Lấy command template từ vendor service"""
        try:
            response = self.vendor_service.get_command_template_by_id(command_id)
            return response
        except Exception as e:
            raise ValueError(f"Failed to get command template {command_id}: {e}")