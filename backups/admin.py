from django.contrib import admin
from .models import BackupAuditEvent, BackupJob


@admin.register(BackupJob)
class BackupJobAdmin(admin.ModelAdmin):
    list_display = ("created_at", "status", "archive_name", "size_bytes", "encrypted", "cloud_status")
    list_filter = ("status", "encrypted", "cloud_status")
    readonly_fields = [field.name for field in BackupJob._meta.fields]


@admin.register(BackupAuditEvent)
class BackupAuditEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "actor", "backup", "ip_address")
    readonly_fields = [field.name for field in BackupAuditEvent._meta.fields]

