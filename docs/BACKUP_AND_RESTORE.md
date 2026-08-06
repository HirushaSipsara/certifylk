# Backup and restore

## What is backed up

`infra/production/scripts/backup.sh` creates a timestamped directory under `BACKUP_DIR` containing:

- `database.dump`: PostgreSQL custom-format logical dump;
- `uploads.tar.gz`: local evidence upload volume;
- `release.env`: UTC timestamp, application image tag, and checked-out commit;
- `SHA256SUMS`: integrity hashes;
- `COMPLETE`: written only after the backup is complete.

Partial directories begin with `.partial-` and are not valid backups. Completed directories older than `BACKUP_RETENTION_DAYS` are pruned. The script exits safely without creating a backup when the production database volume does not yet exist.

Run and verify a backup:

```bash
cd /opt/certifylk/repository
bash infra/production/scripts/backup.sh
BACKUP=/var/backups/certifylk/20260806T120000Z-0123456789ab
cd "$BACKUP"
test -f COMPLETE
sha256sum --check SHA256SUMS
```

Copy backups to an approved encrypted off-host destination. A backup kept only on the same EBS volume does not protect against host or volume loss. S3 integration is not implemented by the application in this stage.

## Restore rules

Restore is a destructive, operator-approved incident operation. It replaces production database/upload state. Confirm the exact backup directory, its hashes, the release commit, and a maintenance window. Take a fresh backup of the current state first unless the incident response lead explicitly prohibits it.

The schema is not automatically downgraded by application rollback. Prefer restoring an application release and database backup known to be compatible. Review every Alembic migration between the backup and target release.

## Database restore

From the exact checked-out compatible release:

```bash
cd /opt/certifylk/repository
BACKUP=/var/backups/certifylk/20260806T120000Z-0123456789ab
test -f "$BACKUP/COMPLETE"
(cd "$BACKUP" && sha256sum --check SHA256SUMS)
bash infra/production/scripts/backup.sh

docker compose --env-file infra/production/.env.production -f infra/production/docker-compose.yml stop nginx frontend backend
docker compose --env-file infra/production/.env.production -f infra/production/docker-compose.yml up -d --wait postgres

cat "$BACKUP/database.dump" | docker compose \
  --env-file infra/production/.env.production \
  -f infra/production/docker-compose.yml \
  exec -T postgres sh -c 'pg_restore --clean --if-exists --no-owner --no-privileges --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"'
```

`--clean` removes database objects represented by the backup before recreating them. Confirm the command and backup again before running it.

## Upload restore

The following command deletes the current upload volume contents before expanding the selected archive. Confirm `BACKUP` resolves beneath `/var/backups/certifylk` and the archive hash has passed:

```bash
BACKUP=/var/backups/certifylk/20260806T120000Z-0123456789ab
case "$BACKUP" in /var/backups/certifylk/20*-*) ;; *) echo "Unsafe backup path" >&2; exit 1 ;; esac

docker run --rm \
  --mount type=volume,source=certifylk-production-uploads,target=/restore \
  --mount type=bind,source="$BACKUP",target=/backup,readonly \
  alpine:3.22 \
  sh -c 'find /restore -mindepth 1 -delete && tar -xzf /backup/uploads.tar.gz -C /restore --strip-components=1'
```

Reapply ownership and start the compatible application release:

```bash
docker compose --env-file infra/production/.env.production -f infra/production/docker-compose.yml up --no-deps upload-init
bash infra/production/scripts/migrate.sh
docker compose --env-file infra/production/.env.production -f infra/production/docker-compose.yml up -d --wait backend frontend nginx
bash infra/production/scripts/health-check.sh
```

## Restore verification

- Public `/`, `/api/v1/health`, and `/api/v1/ready` return success over HTTPS.
- A known restored assessment and evidence file can be retrieved.
- The one-click chilli-paste sample completes and shows strengths, gaps, LKR costs, and the disclaimer.
- Alembic reports the expected head.
- Container logs contain no restore or permission errors.
- Record the incident, backup name, compatible image SHA, operator, and verification results.

Test this procedure on a non-production host at least quarterly and after migration/storage changes.
