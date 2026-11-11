from django.contrib import messages
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .access import backup_admin_required
from .models import BackupAuditEvent, BackupJob
from core.crud_support import identifier_lookup
from .services import BackupError, create_backup, restore_backup as restore_backup_archive, verify_backup


def _ip(request):
    return request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "")).split(",")[0].strip() or None


@backup_admin_required
def dashboard(request):
    jobs = BackupJob.objects.select_related("created_by")[:50]
    audits = BackupAuditEvent.objects.select_related("actor", "backup")[:20]
    return render(request, "backups/dashboard.html", {"jobs": jobs, "audits": audits})


@backup_admin_required
def run_backup(request):
    if request.method != "POST":
        return redirect("backups:dashboard")
    try:
        job = create_backup(user=request.user)
        messages.success(request, f"Backup completed and verified: {job.archive_name}")
    except BackupError as exc:
        messages.error(request, f"Backup failed: {exc}")
    return redirect("backups:dashboard")


@backup_admin_required
def download_backup(request, pk):
    job = get_object_or_404(BackupJob, status__in=[BackupJob.Status.SUCCESS, BackupJob.Status.RESTORED], **identifier_lookup(pk))
    if not verify_backup(job):
        messages.error(request, "The backup failed integrity verification and cannot be downloaded.")
        return redirect("backups:dashboard")
    BackupAuditEvent.objects.create(action="download", actor=request.user, backup=job, ip_address=_ip(request))
    return FileResponse(open(job.archive_path, "rb"), as_attachment=True, filename=job.archive_name)


@backup_admin_required
def restore_backup(request, pk):
    job = get_object_or_404(BackupJob, **identifier_lookup(pk))
    if request.method != "POST":
        return redirect("backups:dashboard")
    try:
        restore_backup_archive(job)
        # The restored database contains the pre-finalisation version of the
        # backup row. Rehydrate its metadata, but keep the backup itself
        # successful; the restore action is represented by the audit event.
        restored_job = BackupJob.objects.get(pk=job.pk)
        restored_job.archive_name = job.archive_name
        restored_job.archive_path = job.archive_path
        restored_job.sha256 = job.sha256
        restored_job.size_bytes = job.size_bytes
        restored_job.encrypted = job.encrypted
        restored_job.cloud_status = job.cloud_status
        restored_job.status = BackupJob.Status.SUCCESS
        restored_job.completed_at = job.completed_at
        restored_job.save(update_fields=["archive_name", "archive_path", "sha256", "size_bytes", "encrypted", "cloud_status", "status", "completed_at"])
        BackupAuditEvent.objects.create(action="restore", actor=request.user, backup=restored_job, ip_address=_ip(request), detail=f"Restored at {timezone.now().isoformat()}")
        messages.success(request, f"Database restored from {job.archive_name}. Restart the web worker if PythonAnywhere has cached connections.")
    except BackupError as exc:
        messages.error(request, f"Restore failed: {exc}")
    return redirect("backups:dashboard")
