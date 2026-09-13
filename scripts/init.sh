#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -f .env ]]; then
  echo ".env already exists. Nothing changed."
  exit 0
fi

cp .env.example .env
DB_PASS="$(openssl rand -hex 24)"
REDIS_PASS="$(openssl rand -hex 24)"
sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=${DB_PASS}/" .env
sed -i "s/^REDIS_PASSWORD=.*/REDIS_PASSWORD=${REDIS_PASS}/" .env

echo "Created .env with random PostgreSQL and Redis passwords."
echo "Edit DOMAIN and CF_TUNNEL_TOKEN later only if you want a public domain."
