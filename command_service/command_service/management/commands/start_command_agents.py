from django.conf import settings
from django.core.management.base import BaseCommand
import threading
import time
from commands.agents.command_agent import CommandAgent

class Command(BaseCommand):
    help = 'Start command processing agents'
    
    def add_arguments(self, parser):
        parser.add_argument('--agents', type=int, default=1, help='Number of agents')
        parser.add_argument('--priority-agents', type=int, default=1, help='Number of priority agents')
    
    def handle(self, *args, **options):
        agents = []
        
        # Start normal agents
        for i in range(options['agents']):
            agent = CommandAgent(agent_id=f"agent-{i}")
            thread = threading.Thread(target=agent.start)
            thread.daemon = True
            thread.start()
            agents.append(agent)
        
        self.stdout.write(f"Started {len(agents)} command agents")
        
        # Keep running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stdout.write("Shutting down agents...")