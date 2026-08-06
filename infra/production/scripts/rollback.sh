#!/usr/bin/env bash

set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

requested_tag="${1:-}"
load_environment
ensure_state_directories
require_command docker
require_command curl
acquire_deployment_lock

current_file="$RELEASE_STATE_DIR/current"
previous_file="$RELEASE_STATE_DIR/previous"
current_tag=""
[[ -f "$current_file" ]] && current_tag="$(tr -d '[:space:]' <"$current_file")"

if [[ -z "$requested_tag" ]]; then
  [[ -f "$previous_file" ]] || die "No previous release is recorded; provide an explicit 40-character image tag."
  requested_tag="$(tr -d '[:space:]' <"$previous_file")"
fi
[[ "$requested_tag" =~ ^[0-9a-f]{40}$ ]] || die "Rollback target must be a full 40-character lowercase Git commit SHA."

export IMAGE_TAG="$requested_tag"
validate_environment
registry_login_if_configured

log "Rolling application containers back to $IMAGE_TAG. Database migrations are intentionally not downgraded."
compose pull upload-init backend frontend
compose up --no-deps upload-init
compose up -d --remove-orphans --wait backend frontend nginx
bash "$SCRIPT_DIR/health-check.sh"

umask 077
if [[ "$current_tag" =~ ^[0-9a-f]{40}$ && "$current_tag" != "$IMAGE_TAG" ]]; then
  printf '%s\n' "$current_tag" >"$previous_file.tmp"
  mv -- "$previous_file.tmp" "$previous_file"
fi
printf '%s\n' "$IMAGE_TAG" >"$current_file.tmp"
mv -- "$current_file.tmp" "$current_file"

log "Rollback to $IMAGE_TAG completed successfully."
