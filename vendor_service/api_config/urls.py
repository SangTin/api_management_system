from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import APIConfigurationViewSet, CommandTemplateViewSet

router = DefaultRouter()
router.register(r'api-configs', APIConfigurationViewSet, basename='apiconfig')
router.register(r'command-templates', CommandTemplateViewSet, basename='commandtemplate')

urlpatterns = [
    path('', include(router.urls)),
]