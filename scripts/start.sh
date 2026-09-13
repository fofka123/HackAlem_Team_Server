#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
[[ -f .env ]] || ./scripts/init.sh
docker compose up -d --build
echo
echo "App: http://127.0.0.1:8080"
