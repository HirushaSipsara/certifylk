#!/usr/bin/env bash

set -Eeuo pipefail

repository_path="${CERTIFYLK_REPOSITORY_PATH:-/opt/certifylk/repository}"
production_dir="$repository_path/infra/production"
docker compose \
  --env-file "$production_dir/.env.production" \
  -f "$production_dir/docker-compose.yml" \
  exec -T nginx nginx -s reload
