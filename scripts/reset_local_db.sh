#!/usr/bin/env bash
set -euo pipefail

read -r -p "Reset the CertifyLK local PostgreSQL database and delete its local volume? [y/N] " reply
if [[ ! "$reply" =~ ^[Yy]$ ]]; then
  echo "Cancelled."
  exit 0
fi

docker compose -f infra/local/docker-compose.yml down -v
docker compose -f infra/local/docker-compose.yml up -d
cd backend
python -m alembic upgrade head
cd ..
python scripts/seed_demo_data.py
echo "Local CertifyLK database reset and seeded."

