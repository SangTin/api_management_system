from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DeviceViewSet, DeviceCommandViewSet

router = DefaultRouter()
router.register(r'devices', DeviceViewSet, basename='device')
router.register(r'device-commands', DeviceCommandViewSet, basename='devicecommand')


urlpatterns = [
    path('', include(router.urls)),
]