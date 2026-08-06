#!/usr/bin/env bash

set -Eeuo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=common.sh
source "$SCRIPT_DIR/common.sh"

load_environment
require_command curl

base_url="${PUBLIC_BASE_URL:-https://${DOMAIN_NAME}}"
attempts="${HEALTHCHECK_ATTEMPTS:-20}"
delay_seconds="${HEALTHCHECK_DELAY_SECONDS:-5}"
curl_args=(--fail --silent --show-error --max-time 15)
if [[ -n "${HEALTHCHECK_CA_CERT:-}" ]]; then
  [[ -f "$HEALTHCHECK_CA_CERT" ]] || die "HEALTHCHECK_CA_CERT does not exist: $HEALTHCHECK_CA_CERT"
  curl_args+=(--cacert "$HEALTHCHECK_CA_CERT")
fi

for ((attempt = 1; attempt <= attempts; attempt += 1)); do
  if curl "${curl_args[@]}" "$base_url/api/v1/health" >/dev/null \
    && curl "${curl_args[@]}" "$base_url/api/v1/ready" >/dev/null \
    && curl "${curl_args[@]}" "$base_url/" >/dev/null; then
    log "Public HTTPS health checks passed at $base_url."
    exit 0
  fi
  log "Health check attempt $attempt/$attempts failed; retrying in ${delay_seconds}s."
  sleep "$delay_seconds"
done

die "Public HTTPS health checks did not pass at $base_url."
