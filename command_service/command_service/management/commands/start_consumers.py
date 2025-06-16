from django.core.management.base import BaseCommand
import threading
import time
import signal
import sys
from commands.consumers.device_command_consumer import DeviceCommandConsumer

class Command(BaseCommand):
    help = 'Start Kafka consumers for command service'
    
    def __init__(self):
        super().__init__()
        self.consumers = []
        self.running = True
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.stdout.write(self.style.WARNING('Received shutdown signal...'))
        self.running = False
        
        # Stop all consumers gracefully
        for consumer in self.consumers:
            if hasattr(consumer, 'stop'):
                consumer.stop()
        
        self.stdout.write(self.style.SUCCESS('All consumers stopped'))
        sys.exit(0)
    
    def handle(self, *args, **options):
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            # Start device command consumer
            device_consumer = DeviceCommandConsumer()
            self.consumers.append(device_consumer)
            
            self.stdout.write(
                self.style.SUCCESS(f"Started {len(self.consumers)} consumers")
            )
            
            # Keep main thread alive
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error starting consumers: {e}")
            )
            sys.exit(1)