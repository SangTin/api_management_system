from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'dashboard-metrics', views.DashboardMetricsViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # Dashboard endpoints
    path('dashboard/overview/', views.dashboard_overview, name='dashboard-overview'),
    path('dashboard/real-time/', views.real_time_metrics, name='real-time-metrics'),
    path('dashboard/refresh/', views.refresh_analytics, name='refresh-analytics'),
    
    # Analytics endpoints
    path('users/', views.user_analytics, name='user-analytics'),
    path('vendors/performance/', views.vendor_performance, name='vendor-performance'),
    path('commands/', views.command_analytics, name='command-analytics'),
    path('system/health/', views.system_health, name='system-health'),
    
    # Export endpoints
    path('export/', views.export_analytics, name='export-analytics'),
]