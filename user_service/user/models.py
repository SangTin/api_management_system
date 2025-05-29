from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
import uuid
import random

class CustomUserManager(UserManager):
    def _create_user(self, username, email, password, **extra_fields):
        if not username:
            # Thêm validation để tránh conflict
            base_username = email.split('@')[0] if email else "user"
            random_suffix = random.randint(100000, 999999)
            username = f"{base_username}_{random_suffix}"
            
            # Ensure unique
            while self.model.objects.filter(username=username).exists():
                random_suffix = random.randint(100000, 999999)
                username = f"{base_username}_{random_suffix}"

        email = self.normalize_email(email) if email else ""
        extra_fields["username"] = username
        extra_fields["email"] = email

        user = self.model(**extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", "admin")
        extra_fields.setdefault("email_verified", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(username, email, password, **extra_fields)

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    organization = models.ForeignKey('organization.Organization', on_delete=models.CASCADE, null=True, blank=True)
    role = models.CharField(max_length=50, choices=[
        ('admin', 'Administrator'),
        ('operator', 'Operator'),
        ('viewer', 'Viewer'),
        ('vendor_admin', 'Vendor Administrator')
    ], default='viewer')
    is_api_user = models.BooleanField(default=False)  # For service-to-service auth
    api_key = models.CharField(max_length=100, blank=True, unique=True, null=True)
    google_id = models.CharField(max_length=100, blank=True, null=True)  # Google OAuth ID
    email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = CustomUserManager()
    USERNAME_FIELD = 'username'
    
    class Meta:
        db_table = 'user_user'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['username']),
            models.Index(fields=['api_key']),
        ]
        
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
        import secrets
        self.api_key = f"ak_{secrets.token_urlsafe(32)}"
        return self.api_key
    
    def regenerate_api_key(self):
        """Regenerate API key and save"""
        self.generate_api_key()
        self.save()
        return self.api_key