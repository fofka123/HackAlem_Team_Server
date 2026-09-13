#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
[[ -f .env ]] || ./scripts/init.sh
docker compose --profile tools up -d portainer uptime-kuma
echo
echo "Portainer: https://127.0.0.1:9443"
echo "Uptime Kuma: http://127.0.0.1:3001"
