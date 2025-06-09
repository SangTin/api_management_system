from django.apps import AppConfig
import os
import threading

class VendorServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'vendor_service'
    
    def ready(self):
        if self.should_start_consumers():
            self.start_consumers()
    
    def should_start_consumers(self):
        """Check if consumers should be started"""
        # TODO: start when START_KAFKA_CONSUMERS is set to True in environment variables
        start_consumers = True
        
        import sys
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
            return False
        
        if 'test' in sys.argv:
            return False
        
        return start_consumers
    
    def start_consumers(self):
        """Start Kafka consumers in background threads"""
        try:
            from vendor_service.consumers.command_template_consumer import CommandTemplateConsumer

            def run_command_template_consumer():
                consumer = CommandTemplateConsumer()
                print("Command template consumer started")

            thread = threading.Thread(target=run_command_template_consumer, daemon=True)
            thread.start()
            
        except Exception as e:
            print(f"Failed to start consumers: {e}")