from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from .services import AnalyticsService
import logging

logger = logging.getLogger(__name__)

class AnalyticsTasks:
    """Class to handle analytics background tasks"""
    
    @staticmethod
    def calculate_daily_metrics():
        """Calculate metrics for yesterday"""
        yesterday = timezone.now().date() - timedelta(days=1)
        analytics_service = AnalyticsService()
        
        try:
            metrics = analytics_service.calculate_daily_metrics(yesterday)
            logger.info(f"Daily metrics calculated for {yesterday}")
            return metrics
        except Exception as e:
            logger.error(f"Error calculating daily metrics: {e}")
            return None
    
    @staticmethod
    def calculate_weekly_metrics():
        """Calculate weekly metrics"""
        # Implementation for weekly aggregation
        pass
    
    @staticmethod
    def calculate_monthly_metrics():
        """Calculate monthly metrics"""
        # Implementation for monthly aggregation
        pass
    
    @staticmethod
    def cleanup_old_metrics():
        """Clean up old analytics data"""
        # Keep last 90 days of daily metrics
        cutoff_date = timezone.now().date() - timedelta(days=90)
        
        from .models import DashboardMetrics
        deleted_count = DashboardMetrics.objects.filter(
            metric_type='daily',
            date__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old daily metrics")
        return deleted_count