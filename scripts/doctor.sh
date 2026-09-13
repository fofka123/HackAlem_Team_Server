#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "=== HackAlem Team Server Doctor ==="
for cmd in docker git openssl curl; do
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "[OK] $cmd -> $(command -v "$cmd")"
  else
    echo "[FAIL] $cmd not found"
  fi
done

echo
echo "Compose validation:"
docker compose config >/dev/null
echo "[OK] compose.yml is valid"

echo
echo "Services:"
docker compose ps || true

echo
echo "Local app health:"
curl -fsS http://127.0.0.1:8080/api/health || true
echo
