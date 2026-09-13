#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
SERVICE="${1:-}"
if [[ -n "$SERVICE" ]]; then
  docker compose logs -f --tail=150 "$SERVICE"
else
  docker compose logs -f --tail=100
fi
