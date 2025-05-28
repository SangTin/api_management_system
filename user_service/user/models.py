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
    api_key = models.CharField(max_length=100, blank=True, unique=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
        
    def clean(self):
        super().clean()
        # Convert empty string to None
        if self.api_key == '':
            self.api_key = None
            
        # Generate API key for API users if not provided
        if self.is_api_user and not self.api_key:
            self.generate_api_key()
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def generate_api_key(self):
        """Generate a new API key"""
        self.api_key = f"ak_{secrets.token_urlsafe(32)}"
        return self.api_key
    
    def regenerate_api_key(self):
        """Regenerate API key and save"""
        self.generate_api_key()
        self.save()
        return self.api_key