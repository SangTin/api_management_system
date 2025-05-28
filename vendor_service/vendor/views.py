from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Vendor
from .serializers import VendorSerializer

class VendorViewSet(viewsets.ModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer

    def get_queryset(self):
        if hasattr(self.request, 'user_role') and self.request.user_role != 'admin':
            return self.queryset.filter(created_by=self.request.user_id)
        return self.queryset

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        vendor = self.get_object()
        vendor.status = 'active'
        vendor.save()
        return Response({'status': 'Vendor activated'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        vendor = self.get_object()
        vendor.status = 'inactive'
        vendor.save()
        return Response({'status': 'Vendor deactivated'})