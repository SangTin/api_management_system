from django.db import models
import uuid

class Vendor(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    contact_info = models.JSONField(default=dict)  # email, phone, address
    description = models.TextField(blank=True)
    website = models.URLField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended')
    ], default='active')
    created_by = models.CharField(max_length=100)  # User ID
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'vendors'
        unique_together = ['code', 'created_by']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.code})"
