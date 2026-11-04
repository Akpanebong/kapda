# KAPDA production backups

The backup command creates a consistent SQLite snapshot using SQLite's online backup API, packages the snapshot together with `media/` and `static/`, encrypts the archive with Fernet, calculates SHA-256, and verifies the archive before it is marked successful.

## Configure

Install the requirements, then generate an encryption key once and store it as a secret environment variable (never commit it):

```text
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
BACKUP_ENCRYPTION_KEY=<generated-key>
BACKUP_ROOT=/home/<pythonanywhere-user>/kapda-backups
```

For Google Drive, configure `rclone` on the PythonAnywhere account and set:

```text
BACKUP_RCLONE_REMOTE=gdrive:kapda-production/backups
```

The remote name must already exist in `rclone config`. If it is blank, backups remain local and the dashboard reports `Not_configured`.

For example, to send every scheduled backup to the host user's Google Drive, log into the PythonAnywhere host account, run `rclone config` once to create a Google Drive remote named `gdrive`, and set `BACKUP_RCLONE_REMOTE=gdrive:kapda-production/backups`. The scheduled task then uploads each successfully verified archive. The encryption key must still be retained separately from Drive.

Local and matching cloud archives older than `BACKUP_RETENTION_DAYS` (default: 7 days) are pruned after each successful backup. Cloud pruning is enabled by `BACKUP_RCLONE_RETENTION=True` and only matches files named `kapda-backup-*.tar.gz.enc`; use a dedicated remote folder for KAPDA backups.

Email is best used for success/failure notifications rather than archive attachments: encrypted backups can exceed normal mail attachment limits. The current dashboard and scheduled command provide the backup status; configure Django's SMTP settings if email notifications are required.

## PythonAnywhere schedule

Create a PythonAnywhere **Scheduled task** that runs once per day, using the same virtualenv as the web application:

```text
/home/<pythonanywhere-user>/.virtualenvs/kapda/bin/python /home/<pythonanywhere-user>/kapda_digital/manage.py run_backup
```

The command exits non-zero on missing encryption configuration, failed verification, or failed cloud upload, so the scheduled-task log can be monitored.

## Operations dashboard

System administrators can open `/backups/` to see history, checksums, cloud status and the audit trail. Download and restore are both restricted to administrators. Restore validates SHA-256, decrypts the archive, runs `PRAGMA integrity_check`, replaces the SQLite database, and merges archived media into `MEDIA_ROOT`.

## Recovery when the website is unavailable

Use a PythonAnywhere console or SSH session from the project directory. The web dashboard is not required:

```text
python manage.py restore_backup --id <backup-history-id> --yes
```

If the backup-history database cannot be read, restore directly from an archive file. The command calculates its SHA-256 automatically, or you can provide the recorded value:

```text
python manage.py restore_backup --archive /home/<pythonanywhere-user>/kapda-backups/kapda-backup-YYYYMMDDTHHMMSSZ.tar.gz.enc --yes
```

Afterward reload the PythonAnywhere web app. This restores database and media data. If the outage was caused by a bad code deployment, also roll back the application source/deployment to the last known-good Git revision; a database restore does not restore Python files, migrations, templates, or installed packages.
