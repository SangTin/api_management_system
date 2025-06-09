from django.conf import settings
from django.core.management.base import BaseCommand
import threading
import time
import signal
import sys
from commands.agents.api_test_agent import APITestAgent
from commands.agents.device_command_agent import DeviceCommandAgent

class Command(BaseCommand):
   help = 'Start command processing agents'
   
   def __init__(self):
       super().__init__()
       self.agents = []
       self.running = True
   
   def add_arguments(self, parser):
       parser.add_argument('--test_agents', type=int, default=1, help='Number of API test agents to start')
       parser.add_argument('--device_agents', type=int, default=2, help='Number of device command agents to start')
   
   def signal_handler(self, signum, frame):
       """Handle shutdown signals"""
       self.stdout.write(self.style.WARNING('Received shutdown signal...'))
       self.running = False
       
       # Stop all agents gracefully
       for agent in self.agents:
           if hasattr(agent, 'stop'):
               agent.stop()
       
       self.stdout.write(self.style.SUCCESS('All agents stopped'))
       sys.exit(0)
   
   def handle(self, *args, **options):
       # Setup signal handlers
       signal.signal(signal.SIGINT, self.signal_handler)
       signal.signal(signal.SIGTERM, self.signal_handler)
       
       threads = []
       
       # Start API test agents
       for i in range(options.get('test_agents', 1)):
           agent = APITestAgent(agent_id=f"test-{i}")
           thread = threading.Thread(
               target=self.run_agent_with_error_handling, 
               args=(agent, 'test'),
               daemon=False  # Không dùng daemon
           )
           thread.start()
           threads.append(thread)
           self.agents.append(agent)
       
       # Start device command agents  
       for i in range(options.get('device_agents', 2)):
           agent = DeviceCommandAgent(agent_id=f"device-{i}")
           thread = threading.Thread(
               target=self.run_agent_with_error_handling, 
               args=(agent, 'device'),
               daemon=False  # Không dùng daemon
           )
           thread.start()
           threads.append(thread)
           self.agents.append(agent)
       
       self.stdout.write(
           self.style.SUCCESS(f"Started {len(self.agents)} command agents")
       )
       
       # Keep main thread alive
       try:
           while self.running:
               time.sleep(1)
               
               # Optional: Check if any thread died
               dead_threads = [t for t in threads if not t.is_alive()]
               if dead_threads:
                   self.stdout.write(
                       self.style.WARNING(f"{len(dead_threads)} agent threads died")
                   )
               
       except KeyboardInterrupt:
           self.signal_handler(signal.SIGINT, None)
   
   def run_agent_with_error_handling(self, agent, agent_type):
       """Run agent with proper error handling"""
       try:
           self.stdout.write(f'Starting {agent_type} agent {agent.agent_id}...')
           agent.start_consumer()  # This should block
           
       except Exception as e:
           self.stdout.write(
               self.style.ERROR(f'Agent {agent.agent_id} failed: {e}')
           )
           # Wait before potential restart
           time.sleep(5)
           
           # Optional: Restart agent
           if self.running:
               self.stdout.write(f'Restarting agent {agent.agent_id}...')
               self.run_agent_with_error_handling(agent, agent_type)