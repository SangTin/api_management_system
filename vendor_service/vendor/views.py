from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Vendor
from .serializers import VendorSerializer
from shared.kafka.publisher import publish_vendor_created, EventPublisher, EventTypes


from shared.permissions import (
    IsAdminUser,
    IsViewer, 
    IsOwnerOrAdmin,
    require_role,
    organization_required,
    PermissionRequiredMixin,
    OrganizationFilterMixin
)

class VendorViewSet(PermissionRequiredMixin, OrganizationFilterMixin, viewsets.ModelViewSet):
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code',]
    ordering_fields = ['name', 'code', 'created_at']
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    
    permission_map = {
        'list': [IsAdminUser],
        'retrieve': [IsOwnerOrAdmin],
        'create': [IsAdminUser],
        'update': [IsOwnerOrAdmin],
        'partial_update': [IsOwnerOrAdmin],
        'destroy': [IsAdminUser],
        'activate': [IsAdminUser],
        'deactivate': [IsAdminUser],
    }
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vendor = serializer.save()
        
        # Publish vendor created event
        publish_vendor_created(
            vendor_id=str(vendor.id),
            vendor_name=vendor.name,
            user_id=str(request.user.id)
        )
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        old_data = {
            'name': instance.name,
            'status': instance.status,
            'description': instance.description
        }
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        vendor = serializer.save()
        
        # Publish vendor updated event
        EventPublisher.publish_vendor_event(
            EventTypes.VENDOR_UPDATED,
            {
                'vendor_id': str(vendor.id),
                'name': vendor.name,
                'old_data': old_data,
                'new_data': {
                    'name': vendor.name,
                    'status': vendor.status,
                    'description': vendor.description
                }
            },
            str(request.user.id)
        )
        
        return Response(serializer.data)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        status = request.query_params.get('status').strip().lower() if request.query_params.get('status') else None
        if status:
            if status in ['active', 'inactive']:
                queryset = queryset.filter(status=status)
            elif status == 'all':
                pass
            else:
                return Response({'error': 'Invalid status filter'}, status=status.HTTP_400_BAD_REQUEST)
        
        days = request.query_params.get('days')
        if days and days.isdigit():
            days = int(days)
            start_date = timezone.now() - timezone.timedelta(days=days)
            queryset = queryset.filter(created_at__gte=start_date)
            
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        total_vendors = Vendor.objects.count()
        active_vendors = Vendor.objects.filter(status='active').count()
        inactive_vendors = Vendor.objects.filter(status='inactive').count()
        
        data = {
            'total_vendors': total_vendors,
            'active_vendors': active_vendors,
            'inactive_vendors': inactive_vendors,
        }
        
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        vendor = self.get_object()
        vendor.status = 'active'
        vendor.save()
        
        # Publish activation event
        EventPublisher.publish_vendor_event(
            EventTypes.VENDOR_ACTIVATED,
            {
                'vendor_id': str(vendor.id),
                'name': vendor.name
            },
            str(request.user.id)
        )
        
        return Response({'status': 'Vendor activated'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        vendor = self.get_object()
        vendor.status = 'inactive'
        vendor.save()
        
        # Publish deactivation event
        EventPublisher.publish_vendor_event(
            EventTypes.VENDOR_DEACTIVATED,
            {
                'vendor_id': str(vendor.id),
                'name': vendor.name
            },
            str(request.user.id)
        )
        
        return Response({'status': 'Vendor deactivated'})