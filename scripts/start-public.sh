#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
[[ -f .env ]] || { echo ".env missing. Run ./scripts/init.sh"; exit 1; }
set -a
source .env
set +a
[[ -n "${CF_TUNNEL_TOKEN:-}" ]] || { echo "CF_TUNNEL_TOKEN is empty."; exit 1; }
docker compose --profile public up -d cloudflared
echo "Cloudflare Tunnel started."
echo "In Cloudflare map your hostname to http://gateway:80"
