from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Avg, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from events.models import EventLog, AuditLog, CommandExecutionLog, SystemMetrics
from .models import DashboardMetrics, SystemHealthMetrics, VendorPerformanceAnalytics
from .serializers import DashboardMetricsSerializer, SystemHealthMetricsSerializer
from .services import AnalyticsService

class DashboardMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet cho dashboard metrics"""
    queryset = DashboardMetrics.objects.all()
    serializer_class = DashboardMetricsSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        metric_type = self.request.query_params.get('type', 'daily')
        days = int(self.request.query_params.get('days', 30))
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        return queryset.filter(
            metric_type=metric_type,
            date__gte=start_date,
            date__lte=end_date
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_overview(request):
    """
    API endpoint để lấy tổng quan dashboard
    """
    try:
        analytics_service = AnalyticsService()
        
        # Get time range from query params
        days = int(request.query_params.get('days', 7))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Calculate overview metrics
        overview = analytics_service.get_dashboard_overview(start_date, end_date)
        
        return Response(overview)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get dashboard overview: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_analytics(request):
    """
    API endpoint để lấy user analytics
    """
    try:
        analytics_service = AnalyticsService()
        
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        analytics = analytics_service.get_user_analytics(start_date, end_date)
        
        return Response(analytics)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get user analytics: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vendor_performance(request):
    """
    API endpoint để lấy vendor performance analytics
    """
    try:
        analytics_service = AnalyticsService()
        
        days = int(request.query_params.get('days', 30))
        vendor_id = request.query_params.get('vendor_id')
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        performance = analytics_service.get_vendor_performance(
            start_date, end_date, vendor_id
        )
        
        return Response(performance)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get vendor performance: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def system_health(request):
    """
    API endpoint để lấy system health metrics
    """
    try:
        analytics_service = AnalyticsService()
        
        hours = int(request.query_params.get('hours', 24))
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=hours)
        
        health = analytics_service.get_system_health(start_time, end_time)
        
        return Response(health)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get system health: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def command_analytics(request):
    """
    API endpoint để lấy command execution analytics
    """
    try:
        analytics_service = AnalyticsService()
        
        days = int(request.query_params.get('days', 7))
        device_id = request.query_params.get('device_id')
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        analytics = analytics_service.get_command_analytics(
            start_date, end_date, device_id
        )
        
        return Response(analytics)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get command analytics: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def real_time_metrics(request):
    """
    API endpoint để lấy real-time metrics
    """
    try:
        analytics_service = AnalyticsService()
        
        # Last hour metrics
        end_time = timezone.now()
        start_time = end_time - timedelta(hours=1)
        
        metrics = analytics_service.get_real_time_metrics(start_time, end_time)
        
        return Response(metrics)
        
    except Exception as e:
        return Response(
            {'error': f'Failed to get real-time metrics: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refresh_analytics(request):
    """
    API endpoint để trigger refresh analytics manually
    """
    try:
        analytics_service = AnalyticsService()
        
        # Refresh today's metrics
        today = timezone.now().date()
        analytics_service.calculate_daily_metrics(today)
        
        return Response({
            'message': 'Analytics refreshed successfully',
            'timestamp': timezone.now().isoformat()
        })
        
    except Exception as e:
        return Response(
            {'error': f'Failed to refresh analytics: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_analytics(request):
    """
    API endpoint để export analytics data
    """
    try:
        analytics_service = AnalyticsService()
        
        export_type = request.query_params.get('type', 'csv')  # csv, json, excel
        days = int(request.query_params.get('days', 30))
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        if export_type == 'csv':
            response = analytics_service.export_to_csv(start_date, end_date)
        elif export_type == 'excel':
            response = analytics_service.export_to_excel(start_date, end_date)
        else:
            response = analytics_service.export_to_json(start_date, end_date)
        
        return response
        
    except Exception as e:
        return Response(
            {'error': f'Failed to export analytics: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )