#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p backups
STAMP="$(date +%Y%m%d_%H%M%S)"
set -a
source .env
set +a
docker compose exec -T postgres pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists > "backups/postgres_${STAMP}.sql"
echo "Backup created: backups/postgres_${STAMP}.sql"
