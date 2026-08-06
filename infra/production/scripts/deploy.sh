#!/usr/bin/env bash

set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

load_environment
validate_environment
ensure_state_directories
require_command docker
require_command curl
acquire_deployment_lock

current_file="$RELEASE_STATE_DIR/current"
previous_file="$RELEASE_STATE_DIR/previous"
failed_file="$RELEASE_STATE_DIR/failed"
previous_tag=""
if [[ -f "$current_file" ]]; then
  previous_tag="$(tr -d '[:space:]' <"$current_file")"
  [[ "$previous_tag" =~ ^[0-9a-f]{40}$ ]] || die "Stored current release is invalid."
fi

registry_login_if_configured
log "Validating production Compose configuration."
compose --profile operations config --quiet

log "Pulling immutable application release $IMAGE_TAG and pinned service images."
compose --profile operations pull postgres nginx upload-init backend frontend migrate seed

if docker volume inspect "${POSTGRES_VOLUME_NAME:-certifylk-production-postgres-data}" >/dev/null 2>&1; then
  log "Creating a pre-deployment backup."
  BACKUP_RELEASE_TAG="${previous_tag:-$IMAGE_TAG}" IMAGE_TAG="$IMAGE_TAG" bash "$SCRIPT_DIR/backup.sh"
fi

log "Preparing the persistent upload volume."
compose up --no-deps upload-init

IMAGE_TAG="$IMAGE_TAG" bash "$SCRIPT_DIR/migrate.sh"

log "Starting release $IMAGE_TAG."
compose up -d --remove-orphans --wait postgres backend frontend nginx

if ! IMAGE_TAG="$IMAGE_TAG" bash "$SCRIPT_DIR/health-check.sh"; then
  printf '%s\n' "$IMAGE_TAG" >"$failed_file"
  if [[ -n "$previous_tag" && "$previous_tag" != "$IMAGE_TAG" ]]; then
    log "New release failed health checks; restoring application images from $previous_tag."
    export IMAGE_TAG="$previous_tag"
    compose pull upload-init backend frontend
    compose up --no-deps upload-init
    compose up -d --remove-orphans --wait backend frontend nginx
    bash "$SCRIPT_DIR/health-check.sh" || die "Both the new release and automatic application rollback failed health checks."
  fi
  die "Release failed health checks. Database migrations were not downgraded; review the failed release before retrying."
fi

umask 077
if [[ -n "$previous_tag" && "$previous_tag" != "$IMAGE_TAG" ]]; then
  printf '%s\n' "$previous_tag" >"$previous_file.tmp"
  mv -- "$previous_file.tmp" "$previous_file"
fi
printf '%s\n' "$IMAGE_TAG" >"$current_file.tmp"
mv -- "$current_file.tmp" "$current_file"
rm -f -- "$failed_file"

log "Release $IMAGE_TAG is healthy and recorded as current."
