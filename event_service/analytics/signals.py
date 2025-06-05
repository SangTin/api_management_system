from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from events.models import EventLog
from .services import AnalyticsService
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=EventLog)
def update_real_time_metrics(sender, instance, created, **kwargs):
    """
    Update real-time metrics when new events are logged
    """
    if not created:
        return
    
    try:
        # Only process certain event types for real-time updates
        real_time_events = [
            'user_login', 'command_executed', 'command_failed',
            'api_config_tested', 'system_error'
        ]
        
        if instance.event_type not in real_time_events:
            return
        
        # Update hourly metrics for current hour
        current_time = timezone.now()
        analytics_service = AnalyticsService()
        
        # You could add real-time aggregation logic here
        # For now, we'll just log the event
        logger.info(f"Real-time metric update: {instance.event_type} at {current_time}")
        
    except Exception as e:
        logger.error(f"Error updating real-time metrics: {e}")
