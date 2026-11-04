import hashlib
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from backups.models import BackupJob
from backups.services import BackupError, restore_backup


class Command(BaseCommand):
    help = "Restore a verified KAPDA backup from the web console or a PythonAnywhere console."

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--id", type=int, help="BackupJob ID stored in the backup history")
        group.add_argument("--archive", help="Path to an encrypted backup archive")
        parser.add_argument("--sha256", help="Expected SHA-256; required only when --archive is used")
        parser.add_argument("--yes", action="store_true", help="Confirm replacement of the live database")

    def handle(self, *args, **options):
        if not options["yes"]:
            raise CommandError("This replaces the live database. Re-run with --yes after confirming the archive.")
        if options["id"]:
            try:
                job = BackupJob.objects.get(pk=options["id"])
            except BackupJob.DoesNotExist as exc:
                raise CommandError("That backup history record does not exist.") from exc
        else:
            archive = Path(options["archive"]).resolve()
            if not archive.exists():
                raise CommandError(f"Archive not found: {archive}")
            checksum = options["sha256"] or self._sha256(archive)
            job = BackupJob(archive_path=str(archive), archive_name=archive.name, sha256=checksum, encrypted=True)
        try:
            restore_backup(job)
        except BackupError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"Restored and integrity-checked {job.archive_name}. Restart/reload the web application."))

    @staticmethod
    def _sha256(path):
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        return digest.hexdigest()

