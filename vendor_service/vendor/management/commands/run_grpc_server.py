from django.core.management.base import BaseCommand
import os
import grpc
import threading
from concurrent import futures
import shared.grpc.generated.vendor_service_pb2_grpc as vendor_service_pb2_grpc
import time
import signal
import sys

from vendor_service.grpc_server import VendorServiceServicer

class Command(BaseCommand):
    help = 'Run the Vendor Service gRPC server'
    
    def __init__(self):
        super().__init__()
        self.server = None
        self.running = True
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.stdout.write(self.style.WARNING('Received shutdown signal...'))
        self.running = False
        
        if self.server:
            self.stdout.write(self.style.WARNING('Stopping gRPC server...'))
            self.server.stop(0)
        
        self.stdout.write(self.style.SUCCESS('gRPC server stopped'))
        sys.exit(0)
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--port', 
            type=int, 
            default=50051, 
            help='Port to run the gRPC server on'
        )
    
    def handle(self, *args, **options):
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        port = options['port']
        self.stdout.write(f"Starting Vendor Service gRPC server on port {port}")
        
        # Create gRPC server
        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        vendor_service_pb2_grpc.add_VendorServiceServicer_to_server(VendorServiceServicer(), self.server)
        
        # Start server
        server_address = f"[::]:{port}"
        self.server.add_insecure_port(server_address)
        self.server.start()
        
        self.stdout.write(self.style.SUCCESS(f"Vendor Service gRPC server running on {server_address}"))
        
        # Keep the server running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.signal_handler(signal.SIGINT, None)