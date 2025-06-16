from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CommandExecutionViewSet

router = DefaultRouter()
router.register(r'command-executions', CommandExecutionViewSet, basename='commandexecution')

urlpatterns = [
    path('api/', include(router.urls)),
]