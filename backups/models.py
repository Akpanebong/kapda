from django.conf import settings
from django.db import models
from django.utils.text import slugify


class BackupJob(models.Model):
    class Status(models.TextChoices):
        RUNNING = "running", "Running"
        SUCCESS = "success", "Successful"
        FAILED = "failed", "Failed"
        RESTORED = "restored", "Restored"

    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.RUNNING)
    archive_name = models.CharField(max_length=255, blank=True)
    archive_path = models.CharField(max_length=1024, blank=True)
    sha256 = models.CharField(max_length=64, blank=True)
    size_bytes = models.PositiveBigIntegerField(default=0)
    encrypted = models.BooleanField(default=True)
    cloud_status = models.CharField(max_length=30, default="not_configured")
    error_message = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="backup_jobs",
    )
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True, editable=False, db_index=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            super().save(*args, **kwargs)
            self.slug = f"{slugify(self.archive_name or 'backup')[:220]}-{self.pk}"
            type(self).objects.filter(pk=self.pk).update(slug=self.slug)
            return
        super().save(*args, **kwargs)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.archive_name or f"Backup {self.pk}"


class BackupAuditEvent(models.Model):
    action = models.CharField(max_length=40)
    detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="backup_audit_events",
    )
    backup = models.ForeignKey(BackupJob, null=True, blank=True, on_delete=models.SET_NULL, related_name="audit_events")
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
