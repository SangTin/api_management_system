from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    organization = models.ForeignKey('organization.Organization', on_delete=models.CASCADE, null=True)
    role = models.CharField(max_length=50, choices=[
        ('admin', 'Administrator'),
        ('operator', 'Operator'),
        ('viewer', 'Viewer'),
        ('vendor_admin', 'Vendor Administrator')
    ])
    is_api_user = models.BooleanField(default=False)  # For service-to-service auth
    api_key = models.CharField(max_length=100, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)