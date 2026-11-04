import hashlib
import json
import logging
import os
import shutil
import sqlite3
import subprocess
import tarfile
import tempfile
from datetime import timedelta
from pathlib import Path
from django.conf import settings
from django import db
from django.utils import timezone
from .models import BackupAuditEvent, BackupJob

logger = logging.getLogger(__name__)


class BackupError(Exception):
    pass


def _setting(name, default):
    return getattr(settings, name, default)


def _key():
    value = os.getenv("BACKUP_ENCRYPTION_KEY", "").strip()
    if not value:
        raise BackupError("BACKUP_ENCRYPTION_KEY is not configured. Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")
    try:
        from cryptography.fernet import Fernet
        return Fernet(value.encode())
    except Exception as exc:
        raise BackupError("BACKUP_ENCRYPTION_KEY is invalid; it must be a Fernet key.") from exc


def _database_path():
    config = settings.DATABASES["default"]
    if config["ENGINE"] != "django.db.backends.sqlite3" or not config.get("NAME"):
        raise BackupError("The configured database is not SQLite; this backup workflow is designed for SQLite production deployments.")
    return Path(config["NAME"]).resolve()


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _rclone_upload(path):
    remote = os.getenv("BACKUP_RCLONE_REMOTE", "").strip()
    if not remote:
        return "not_configured"
    binary = os.getenv("BACKUP_RCLONE_BINARY", "rclone")
    try:
        result = subprocess.run([binary, "copyto", str(path), f"{remote.rstrip('/')}/{path.name}"], capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BackupError(f"rclone upload failed: {exc}") from exc
    if result.returncode:
        raise BackupError(f"rclone upload failed: {result.stderr[-500:]}")
    return "uploaded"


def _rclone_prune():
    """Remove only KAPDA archives older than the configured retention period."""
    remote = os.getenv("BACKUP_RCLONE_REMOTE", "").strip()
    if not remote or os.getenv("BACKUP_RCLONE_RETENTION", "true").strip().lower() not in {"1", "true", "yes", "on"}:
        return
    binary = os.getenv("BACKUP_RCLONE_BINARY", "rclone")
    retention_days = max(int(os.getenv("BACKUP_RETENTION_DAYS", "7")), 1)
    try:
        result = subprocess.run(
            [binary, "delete", remote, "--min-age", f"{retention_days * 24}h", "--include", "kapda-backup-*.tar.gz.enc"],
            capture_output=True, text=True, timeout=300,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        logger.warning("Could not prune old cloud backups: %s", exc)
        return
    if result.returncode:
        logger.warning("Could not prune old cloud backups: %s", result.stderr[-500:])


def _prune_local_backups(current_job):
    retention_days = max(int(os.getenv("BACKUP_RETENTION_DAYS", "7")), 1)
    cutoff = timezone.now() - timedelta(days=retention_days)
    root = Path(_setting("BACKUP_ROOT", settings.BASE_DIR / "backup_storage")).resolve()
    old_jobs = BackupJob.objects.filter(created_at__lt=cutoff).exclude(pk=current_job.pk)
    for old_job in old_jobs:
        if old_job.archive_path:
            path = Path(old_job.archive_path).resolve()
            if path.parent == root and path.exists():
                try:
                    path.unlink()
                except OSError as exc:
                    logger.warning("Could not delete old backup %s: %s", path, exc)
                    continue
        old_job.delete()


def create_backup(user=None):
    database = _database_path()
    if not database.exists():
        raise BackupError(f"Database file does not exist: {database}")
    root = Path(_setting("BACKUP_ROOT", settings.BASE_DIR / "backup_storage"))
    root.mkdir(parents=True, exist_ok=True)
    timestamp = timezone.now().strftime("%Y%m%dT%H%M%SZ")
    archive_name = f"kapda-backup-{timestamp}.tar.gz.enc"
    target = root / archive_name
    job = BackupJob.objects.create(archive_name=archive_name, archive_path=str(target), created_by=user, encrypted=True)
    try:
        with tempfile.TemporaryDirectory(prefix="kapda-backup-") as work:
            workdir = Path(work)
            snapshot = workdir / "database.sqlite3"
            source = sqlite3.connect(str(database))
            destination = sqlite3.connect(str(snapshot))
            try:
                source.backup(destination)
            finally:
                destination.close()
                source.close()
            manifest = {"format": 1, "created_at": timezone.now().isoformat(), "database_sha256": _sha256(snapshot), "includes": ["database.sqlite3", "media/", "static/"]}
            (workdir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            media = Path(settings.MEDIA_ROOT)
            static = Path(settings.BASE_DIR) / "static"
            plaintext = workdir / "archive.tar.gz"
            with tarfile.open(plaintext, "w:gz") as archive:
                archive.add(snapshot, arcname="database.sqlite3")
                archive.add(workdir / "manifest.json", arcname="manifest.json")
                if media.exists():
                    archive.add(media, arcname="media")
                if static.exists():
                    archive.add(static, arcname="static")
            encrypted = _key().encrypt(plaintext.read_bytes())
            target.write_bytes(encrypted)
        job.sha256 = _sha256(target)
        job.size_bytes = target.stat().st_size
        if not verify_backup(job):
            raise BackupError("The newly created archive failed verification.")
        job.cloud_status = _rclone_upload(target)
        job.status = BackupJob.Status.SUCCESS
        job.completed_at = timezone.now()
        job.save(update_fields=["sha256", "size_bytes", "cloud_status", "status", "completed_at"])
        BackupAuditEvent.objects.create(action="create", actor=user, backup=job, detail=f"SHA-256: {job.sha256}")
        _prune_local_backups(job)
        _rclone_prune()
        return job
    except Exception as exc:
        job.status = BackupJob.Status.FAILED
        job.error_message = str(exc)
        job.completed_at = timezone.now()
        job.save(update_fields=["status", "error_message", "completed_at"])
        if isinstance(exc, BackupError):
            raise
        raise BackupError(str(exc)) from exc


def _decrypt_archive(job, workdir):
    path = Path(job.archive_path)
    if not path.exists() or _sha256(path) != job.sha256:
        raise BackupError("Archive is missing or its SHA-256 checksum does not match the recorded value.")
    from cryptography.fernet import InvalidToken
    try:
        raw = _key().decrypt(path.read_bytes())
    except InvalidToken as exc:
        raise BackupError("Archive decryption failed; check BACKUP_ENCRYPTION_KEY.") from exc
    archive = workdir / "archive.tar.gz"
    archive.write_bytes(raw)
    return archive


def verify_backup(job):
    try:
        with tempfile.TemporaryDirectory(prefix="kapda-verify-") as work:
            archive_path = _decrypt_archive(job, Path(work))
            with tarfile.open(archive_path, "r:gz") as archive:
                names = set(archive.getnames())
                if "database.sqlite3" not in names or "manifest.json" not in names:
                    return False
                member = archive.extractfile("database.sqlite3")
                manifest = json.load(archive.extractfile("manifest.json"))
                return member is not None and hashlib.sha256(member.read()).hexdigest() == manifest.get("database_sha256")
    except (BackupError, OSError, tarfile.TarError, json.JSONDecodeError):
        return False


def restore_backup(job):
    if not verify_backup(job):
        raise BackupError("Archive verification failed; restore was stopped.")
    database = _database_path()
    with tempfile.TemporaryDirectory(prefix="kapda-restore-") as work:
        workdir = Path(work)
        archive_path = _decrypt_archive(job, workdir)
        with tarfile.open(archive_path, "r:gz") as archive:
            member = archive.getmember("database.sqlite3")
            extracted = archive.extractfile(member)
            if extracted is None:
                raise BackupError("Archive does not contain a database snapshot.")
            replacement = workdir / "database.sqlite3"
            replacement.write_bytes(extracted.read())
        check = sqlite3.connect(str(replacement))
        try:
            if check.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise BackupError("Restored SQLite snapshot failed integrity_check.")
        finally:
            check.close()
        # Close Django's open SQLite handle before replacing the file. This is
        # important on Windows and prevents a connection from continuing to
        # point at the pre-restore inode on Unix-like hosts.
        db.connections.close_all()
        shutil.copy2(replacement, database)
        # Media is application data and is restored alongside the database.
        # Extract into a temporary directory first so a corrupt archive cannot
        # partially overwrite the live media directory.
        with tarfile.open(archive_path, "r:gz") as archive:
            media_members = [member for member in archive.getmembers() if member.name == "media" or member.name.startswith("media/")]
            if media_members:
                extracted_media = workdir / "media"
                for member in media_members:
                    # Archives are produced locally by this service, but keep
                    # extraction constrained to the temporary restore folder.
                    archive.extract(member, workdir)
                if extracted_media.exists():
                    live_media = Path(settings.MEDIA_ROOT)
                    live_media.mkdir(parents=True, exist_ok=True)
                    for item in extracted_media.iterdir():
                        destination = live_media / item.name
                        if item.is_dir():
                            shutil.copytree(item, destination, dirs_exist_ok=True)
                        else:
                            shutil.copy2(item, destination)
