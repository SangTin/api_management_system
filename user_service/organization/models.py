from django.db import models
import uuid

class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    type = models.CharField(max_length=50, choices=[
        ('government', 'Government'),
        ('vendor', 'Vendor'),
        ('integrator', 'System Integrator')
    ])
    description = models.TextField(blank=True)
    settings = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)