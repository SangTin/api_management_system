from shared.kafka import kafka_service
from shared.kafka.topics import Topics, EventTypes
from device.models import DeviceCommand
from django.utils import timezone

class CommandTemplateConsumer:
    def __init__(self):
        kafka_service.create_consumer(
            topics=[Topics.VENDOR_EVENTS],
            group_id='vendor-template-processor',
            message_handler=self.handle_template_event
        )
    
    def handle_template_event(self, message):
        try:
            event_data = message.get('data', {})
            event_type = message.get('event_type')
            
            if event_type == EventTypes.COMMAND_TEMPLATE_DELETED:
                self.handle_template_deleted(event_data)
                
        except Exception as e:
            print(f"Error processing template event: {e}")
    
    def handle_template_deleted(self, event_data):
        """Handle template deletion - disconnect affected DeviceCommands"""
        template_id = event_data.get('template_id')
        affected_commands_data = event_data.get('affected_device_commands', [])
        
        if not affected_commands_data:
            print(f"No device commands affected by template {template_id} deletion")
            return
        
        affected_command_ids = [cmd['id'] for cmd in affected_commands_data]
        affected_commands = DeviceCommand.objects.filter(id__in=affected_command_ids)
        
        disconnected_count = 0
        for device_cmd in affected_commands:
            device_cmd.soft_delete(reason="CommandTemplate soft deleted")
            disconnected_count += 1
        
        print(f"Disconnected {disconnected_count} device commands due to template deletion")