from django.apps import AppConfig

class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analytics'
    
    def ready(self):
        """Initialize analytics when app is ready"""
        from . import signals