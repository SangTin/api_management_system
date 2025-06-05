from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import filters

from shared.permissions import (
    IsAdminUser,
    IsViewer, 
    IsOwnerOrAdmin,
    require_role,
    organization_required,
    PermissionRequiredMixin,
    OrganizationFilterMixin
)
from .serializers import UserSerializer, UserCreateSerializer

User = get_user_model()

class UserViewSet(PermissionRequiredMixin, OrganizationFilterMixin, viewsets.ModelViewSet):
    """ViewSet cho User management"""
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['email', 'first_name', 'last_name', 'created_at']
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_map = {
        'list': [IsAdminUser],
        'retrieve': [IsOwnerOrAdmin],
        'create': [IsAdminUser],
        'update': [IsOwnerOrAdmin],
        'partial_update': [IsOwnerOrAdmin],
        'destroy': [IsAdminUser],
        'me': [IsViewer],
        'change_password': [IsOwnerOrAdmin],
    }
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    def update(self, request, *args, **kwargs):
        """Override update để chỉ cho phép user update một số fields nhất định"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Chỉ cho phép update một số fields
        allowed_fields = ['first_name', 'last_name', 'phone', 'username']
        data = {k: v for k, v in request.data.items() if k in allowed_fields}
        
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        print(f"User {instance.username} updated with data: {data}")
        
        return Response(serializer.data)
    
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
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

    def _start_of_month(self, date):
        """Trả về ngày đầu tháng của một ngày"""
        return date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    @action(detail=False, methods=['get', 'put'])
    def me(self, request):
        """Endpoint để user xem/edit profile của chính mình"""
        user = request.user
        
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        
        elif request.method == 'PUT':
            # Chỉ cho phép update một số fields
            allowed_fields = ['first_name', 'last_name', 'phone']
            data = {k: v for k, v in request.data.items() if k in allowed_fields}
            
            serializer = self.get_serializer(user, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Endpoint để user đổi password"""
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not user.check_password(old_password):
            return Response(
                {'error': 'Mật khẩu cũ không đúng'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        
        return Response({'message': 'Đổi mật khẩu thành công'})
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def reset_password(self, request, pk=None):
        """Admin reset password cho user"""
        user = self.get_object()
        new_password = request.data.get('new_password', 'temp123456')
        
        user.set_password(new_password)
        user.save()
        
        return Response({
            'message': f'Reset password thành công cho user {user.username}',
            'new_password': new_password
        })
        
    @action(detail=True, methods=['patch'], permission_classes=[IsAdminUser])
    def toggle_status(self, request, pk=None):
        """Admin enable/disable user"""
        user = self.get_object()
        user.is_active = not user.is_active
        user.save()
        
        status_text = 'kích hoạt' if user.is_active else 'vô hiệu hóa'
        return Response({
            'message': f'Đã {status_text} user {user.username}',
            'is_active': user.is_active
        })
        
    @action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
    def statistics(self, request):
        """Endpoint để lấy thống kê user"""
        today = timezone.now()
        start_of_month = self._start_of_month(today)
        
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        new_users_this_month = User.objects.filter(
            created_at__gte=start_of_month
        ).count()
        
        return Response({
            'total_users': total_users,
            'active_users': active_users,
            'new_users_this_month': new_users_this_month
        })