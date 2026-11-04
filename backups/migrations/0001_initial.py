from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="BackupJob",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("status", models.CharField(choices=[("running", "Running"), ("success", "Successful"), ("failed", "Failed"), ("restored", "Restored")], default="running", max_length=20)),
                ("archive_name", models.CharField(blank=True, max_length=255)),
                ("archive_path", models.CharField(blank=True, max_length=1024)),
                ("sha256", models.CharField(blank=True, max_length=64)),
                ("size_bytes", models.PositiveBigIntegerField(default=0)),
                ("encrypted", models.BooleanField(default=True)),
                ("cloud_status", models.CharField(default="not_configured", max_length=30)),
                ("error_message", models.TextField(blank=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="backup_jobs", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ("-created_at",)},
        ),
        migrations.CreateModel(
            name="BackupAuditEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=40)),
                ("detail", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="backup_audit_events", to=settings.AUTH_USER_MODEL)),
                ("backup", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="audit_events", to="backups.backupjob")),
            ],
            options={"ordering": ("-created_at",)},
        ),
    ]
