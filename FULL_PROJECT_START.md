# HackAlem Team Server — Full Project

В архиве объединены:
- React/Vite Team Console
- FastAPI backend
- PostgreSQL + Redis
- Caddy gateway
- Portainer + Uptime Kuma profiles
- Tailscale-compatible Vite host configuration
- GitHub Actions CI
- HackAlem Developer Center для локальной автоматизации Git/тестов/PR

## Первый запуск

```bash
cp .env.example .env
chmod +x scripts/*.sh
./scripts/init.sh
./scripts/start-dev.sh
./scripts/start-tools.sh
```

Team Console: http://127.0.0.1:8080
Portainer: https://127.0.0.1:9443
Uptime Kuma: http://127.0.0.1:3001

## Developer Center

```bash
./scripts/install-dev-center.sh
```

После установки: http://127.0.0.1:8766

Developer Center умеет:
- создавать feature/* ветку от актуального dev;
- запускать локальные проверки;
- commit + push;
- создавать Pull Request в dev;
- ждать GitHub CI и по кнопке выполнять merge.

## Tailscale

Текущий разрешенный Vite hostname:
`cachyos-x8664.tail2347e7.ts.net`

Для другого сервера измените `frontend/vite.config.ts` -> `server.allowedHosts`.
