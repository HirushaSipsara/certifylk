#!/usr/bin/env bash

set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

load_environment
validate_environment
require_command docker

log "Starting PostgreSQL and waiting for readiness."
compose up -d --wait postgres

log "Applying Alembic migrations for release $IMAGE_TAG."
compose run --rm migrate

log "Synchronizing the deterministic requirements, question, recommendation, and cost catalogue."
compose run --rm seed

log "Migrations and catalogue synchronization completed."
