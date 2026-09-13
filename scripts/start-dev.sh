#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
[[ -f .env ]] || ./scripts/init.sh
docker compose -f compose.yml -f compose.dev.yml up -d --build
echo
echo "Development environment: http://127.0.0.1:8080"
