#!/usr/bin/env bash

set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

load_environment
validate_environment
ensure_state_directories
require_command docker
require_command tar
require_command sha256sum

database_volume="${POSTGRES_VOLUME_NAME:-certifylk-production-postgres-data}"
uploads_volume="${UPLOADS_VOLUME_NAME:-certifylk-production-uploads}"
if ! docker volume inspect "$database_volume" >/dev/null 2>&1; then
  log "No production database volume exists yet; no backup is required."
  exit 0
fi

timestamp="$(date -u +'%Y%m%dT%H%M%SZ')"
release_label="${IMAGE_TAG:0:12}"
final_dir="$BACKUP_DIR/${timestamp}-${release_label}"
staging_dir="$BACKUP_DIR/.partial-${timestamp}-$$"
helper_name="certifylk-backup-$RANDOM-$$"

cleanup() {
  if [[ -n "$helper_name" ]]; then
    docker rm -f "$helper_name" >/dev/null 2>&1 || true
  fi
  if [[ -d "$staging_dir" && "$staging_dir" == "$BACKUP_DIR"/.partial-* ]]; then
    rm -rf -- "$staging_dir"
  fi
}
trap cleanup EXIT

umask 077
mkdir -p "$staging_dir/uploads"

log "Ensuring PostgreSQL is ready for a consistent logical backup."
compose up -d --wait postgres
compose exec -T postgres sh -c 'exec pg_dump --format=custom --no-owner --no-privileges --username="$POSTGRES_USER" --dbname="$POSTGRES_DB"' >"$staging_dir/database.dump"

if docker volume inspect "$uploads_volume" >/dev/null 2>&1; then
  MSYS_NO_PATHCONV=1 docker create --name "$helper_name" \
    --mount "type=volume,source=${uploads_volume},target=/source,readonly" \
    "$(backend_image)" true >/dev/null
  if command -v cygpath >/dev/null 2>&1; then
    host_uploads_dir="$(cygpath -w "$staging_dir/uploads")"
    MSYS_NO_PATHCONV=1 docker cp "$helper_name:/source/." "$host_uploads_dir"
  else
    docker cp "$helper_name:/source/." "$staging_dir/uploads"
  fi
  docker rm "$helper_name" >/dev/null
  helper_name=""
fi

tar -C "$staging_dir" -czf "$staging_dir/uploads.tar.gz" uploads
rm -rf -- "$staging_dir/uploads"
printf 'created_utc=%s\nimage_tag=%s\ngit_commit=%s\n' "$timestamp" "${BACKUP_RELEASE_TAG:-$IMAGE_TAG}" "$(git -C "$REPOSITORY_ROOT" rev-parse HEAD 2>/dev/null || printf unknown)" >"$staging_dir/release.env"
(
  cd "$staging_dir"
  sha256sum database.dump uploads.tar.gz release.env >SHA256SUMS
)
printf 'complete\n' >"$staging_dir/COMPLETE"
mv -- "$staging_dir" "$final_dir"
trap - EXIT

retention_days="${BACKUP_RETENTION_DAYS:-30}"
if [[ "$retention_days" =~ ^[0-9]+$ ]]; then
  find "$BACKUP_DIR" -mindepth 1 -maxdepth 1 -type d -name '20??????T??????Z-*' -mtime "+$retention_days" -exec rm -rf -- {} +
fi

log "Backup completed: $final_dir"
