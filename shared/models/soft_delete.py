from django.db import models
from django.utils import timezone

class SoftDeleteQuerySet(models.QuerySet):
    def delete(self):
        return self.update(
            is_deleted=True,
            deleted_at=timezone.now()
        )
    
    def hard_delete(self):
        return super().delete()
    
    def alive(self):
        return self.filter(is_deleted=False)
    
    def dead(self):
        return self.filter(is_deleted=True)
    
    def with_deleted(self):
        return self

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=False)
    
    def with_deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db)
    
    def only_deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db).filter(is_deleted=True)

class SoftDeleteMixin(models.Model):
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.UUIDField(null=True, blank=True)
    deletion_reason = models.TextField(blank=True)
    
    class Meta:
        abstract = True
    
    def delete(self, using=None, keep_parents=False):
        self.soft_delete()
    
    def hard_delete(self):
        super().delete()
    
    def soft_delete(self, user_id=None, reason=""):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user_id
        self.deletion_reason = reason
        self.save()
    
    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.deletion_reason = ""
        self.save()