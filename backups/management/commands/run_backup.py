from django.core.management.base import BaseCommand, CommandError
from backups.services import BackupError, create_backup


class Command(BaseCommand):
    help = "Create, encrypt, verify, and optionally upload the KAPDA backup."

    def handle(self, *args, **options):
        try:
            job = create_backup()
        except BackupError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"Created {job.archive_name} ({job.sha256})"))

