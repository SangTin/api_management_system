import signal
import sys
import time
from django.core.management.base import BaseCommand
from events.consumers import EventConsumerManager
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Start Kafka consumers for Event Service'
    
    def __init__(self):
        super().__init__()
        self.should_stop = False
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--no-auto-restart',
            action='store_true',
            help='Disable automatic restart on failure',
        )
    
    def handle(self, *args, **options):
        """Main command handler"""
        self.setup_signal_handlers()
        
        self.stdout.write(
            self.style.SUCCESS('Starting Kafka consumers for Event Service...')
        )
        
        # Start consumers
        success = EventConsumerManager.start_consumers()
        if not success:
            self.stderr.write(
                self.style.ERROR('Failed to start Kafka consumers')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS('Kafka consumers started successfully')
        )
        
        # Keep running until signal received
        try:
            while not self.should_stop:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        
        self.stdout.write(
            self.style.WARNING('Shutting down Kafka consumers...')
        )
        
        # Cleanup
        from shared.kafka.service import kafka_service
        kafka_service.close()
        
        self.stdout.write(
            self.style.SUCCESS('Kafka consumers stopped')
        )
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.stdout.write(
                self.style.WARNING(f'Received signal {signum}, shutting down...')
            )
            self.should_stop = True
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)