#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PRODUCTION_DIR="$(cd -- "$SCRIPT_DIR/.." && pwd)"
REPOSITORY_ROOT="$(cd -- "$PRODUCTION_DIR/../.." && pwd)"
ENV_FILE="${CERTIFYLK_ENV_FILE:-$PRODUCTION_DIR/.env.production}"
COMPOSE_FILE="$PRODUCTION_DIR/docker-compose.yml"

log() {
  printf '[CertifyLK] %s\n' "$*"
}

die() {
  printf '[CertifyLK] ERROR: %s\n' "$*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || die "Required command is unavailable: $1"
}

load_environment() {
  [[ -f "$ENV_FILE" ]] || die "Environment file not found: $ENV_FILE"

  local requested_image_tag="${IMAGE_TAG:-}"
  local requested_public_base="${PUBLIC_BASE_URL:-}"
  set -a
  # The production environment file is an administrator-owned trusted file.
  # shellcheck disable=SC1090
  source "$ENV_FILE"
  set +a

  if [[ -n "$requested_image_tag" ]]; then
    export IMAGE_TAG="$requested_image_tag"
  fi
  if [[ -n "$requested_public_base" ]]; then
    export PUBLIC_BASE_URL="$requested_public_base"
  fi
}

validate_environment() {
  [[ "${IMAGE_TAG:-}" =~ ^[0-9a-f]{40}$ ]] || die "IMAGE_TAG must be a full 40-character lowercase Git commit SHA."
  [[ "${GHCR_OWNER:-}" =~ ^[a-z0-9][a-z0-9._-]*$ ]] || die "GHCR_OWNER must be lowercase and registry-safe."
  [[ "${DOMAIN_NAME:-}" =~ ^[A-Za-z0-9.-]+$ ]] || die "DOMAIN_NAME is invalid."
  [[ "$DOMAIN_NAME" != *example.com ]] || die "Replace the example DOMAIN_NAME before deployment."
  [[ -n "${POSTGRES_DB:-}" && -n "${POSTGRES_USER:-}" && -n "${POSTGRES_PASSWORD:-}" ]] || die "PostgreSQL settings are incomplete."
  [[ "$POSTGRES_PASSWORD" != *CHANGE_ME* && "$POSTGRES_PASSWORD" != *REPLACE_* ]] || die "Replace the example PostgreSQL password before deployment."
  [[ -n "${DATABASE_URL:-}" ]] || die "DATABASE_URL is required."
  if [[ "${AI_PROVIDER:-mock}" == "gemini" && -z "${GEMINI_API_KEY:-}" ]]; then
    die "GEMINI_API_KEY is required when AI_PROVIDER=gemini."
  fi
}

compose() {
  local compose_args=(--env-file "$ENV_FILE" -f "$COMPOSE_FILE")
  if [[ -n "${CERTIFYLK_COMPOSE_OVERRIDE:-}" ]]; then
    compose_args+=(-f "$CERTIFYLK_COMPOSE_OVERRIDE")
  fi
  docker compose "${compose_args[@]}" "$@"
}

backend_image() {
  printf 'ghcr.io/%s/certifylk-backend:%s' "$GHCR_OWNER" "$IMAGE_TAG"
}

registry_login_if_configured() {
  local registry_file="${REGISTRY_ENV_FILE:-$PRODUCTION_DIR/.env.registry}"
  if [[ ! -f "$registry_file" ]]; then
    log "No registry credential file found; expecting public GHCR packages or an existing Docker login."
    return 0
  fi

  local existing_owner="$GHCR_OWNER"
  set -a
  # shellcheck disable=SC1090
  source "$registry_file"
  set +a
  export GHCR_OWNER="$existing_owner"
  [[ -n "${GHCR_USERNAME:-}" && -n "${GHCR_TOKEN:-}" ]] || die "Registry file must define GHCR_USERNAME and GHCR_TOKEN."
  printf '%s' "$GHCR_TOKEN" | docker login ghcr.io --username "$GHCR_USERNAME" --password-stdin >/dev/null
}

ensure_state_directories() {
  RELEASE_STATE_DIR="${RELEASE_STATE_DIR:-/var/lib/certifylk/releases}"
  BACKUP_DIR="${BACKUP_DIR:-/var/backups/certifylk}"
  [[ "$RELEASE_STATE_DIR" == /* && "$RELEASE_STATE_DIR" != "/" ]] || die "RELEASE_STATE_DIR must be a safe absolute path."
  [[ "$BACKUP_DIR" == /* && "$BACKUP_DIR" != "/" ]] || die "BACKUP_DIR must be a safe absolute path."
  mkdir -p -- "$RELEASE_STATE_DIR" "$BACKUP_DIR"
  chmod 700 "$RELEASE_STATE_DIR" "$BACKUP_DIR"
  export RELEASE_STATE_DIR BACKUP_DIR
}

acquire_deployment_lock() {
  require_command flock
  exec 9>"$RELEASE_STATE_DIR/deploy.lock"
  flock -n 9 || die "Another production operation is already running."
}
