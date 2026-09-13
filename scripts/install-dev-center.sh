#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$(command -v python3 || true)"
[[ -n "$PYTHON" ]] || { echo "python3 not found"; exit 1; }
mkdir -p "$HOME/.config/systemd/user" "$HOME/.local/share/applications"
SERVICE="$HOME/.config/systemd/user/hackalem-dev-center.service"
cat > "$SERVICE" <<EOF
[Unit]
Description=HackAlem Developer Center
After=network-online.target

[Service]
Type=simple
WorkingDirectory=$ROOT
ExecStart=$PYTHON $ROOT/scripts/dev_center.py serve --host 127.0.0.1 --port 8766
Restart=on-failure
RestartSec=2

[Install]
WantedBy=default.target
EOF
cat > "$HOME/.local/share/applications/hackalem-dev-center.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=HackAlem Developer Center
Comment=Local Git, Docker and CI workflow for HackAlem
Exec=xdg-open http://127.0.0.1:8766
Terminal=false
Categories=Development;
EOF
chmod +x "$HOME/.local/share/applications/hackalem-dev-center.desktop"
systemctl --user daemon-reload
systemctl --user enable --now hackalem-dev-center.service
sleep 1
systemctl --user --no-pager --full status hackalem-dev-center.service || true
echo
echo "Developer Center installed: http://127.0.0.1:8766"
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open http://127.0.0.1:8766 >/dev/null 2>&1 || true
fi
