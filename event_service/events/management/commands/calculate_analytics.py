from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from analytics.services import AnalyticsService

class Command(BaseCommand):
    help = 'Calculate analytics metrics'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date to calculate metrics for (YYYY-MM-DD format)'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Number of days to calculate (default: 1)'
        )
        parser.add_argument(
            '--type',
            type=str,
            choices=['daily', 'weekly', 'monthly'],
            default='daily',
            help='Type of metrics to calculate'
        )
    
    def handle(self, *args, **options):
        analytics_service = AnalyticsService()
        
        if options['date']:
            # Parse specific date
            try:
                target_date = timezone.datetime.strptime(options['date'], '%Y-%m-%d').date()
            except ValueError:
                self.stderr.write(
                    self.style.ERROR('Invalid date format. Use YYYY-MM-DD')
                )
                return
        else:
            # Default to yesterday
            target_date = timezone.now().date() - timedelta(days=1)
        
        if options['type'] == 'daily':
            # Calculate daily metrics
            for i in range(options['days']):
                calc_date = target_date - timedelta(days=i)
                
                self.stdout.write(f'Calculating daily metrics for {calc_date}...')
                
                try:
                    metrics = analytics_service.calculate_daily_metrics(calc_date)
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Daily metrics calculated for {calc_date}')
                    )
                except Exception as e:
                    self.stderr.write(
                        self.style.ERROR(f'❌ Error calculating metrics for {calc_date}: {e}')
                    )
        
        self.stdout.write(
            self.style.SUCCESS('Analytics calculation completed!')
        )