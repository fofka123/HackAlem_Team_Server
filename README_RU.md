# HackAlem Team Server — сервер на ноутбуке без VPS

Этот набор делает твой ноутбук центральным integration/demo-сервером для команды из 3 человек.

## Что уже есть

- React + Vite frontend;
- FastAPI backend;
- PostgreSQL;
- Redis;
- Caddy gateway;
- отдельные Docker-контейнеры и healthcheck;
- Portainer GUI для Docker;
- Uptime Kuma для мониторинга;
- dev и production режимы;
- Git workflow + отдельные CI jobs для frontend/backend;
- Tailscale для приватного доступа команды;
- Cloudflare Tunnel как опция для публичного домена без VPS и без проброса портов.

## Почему ошибка frontend не обязана положить backend

Frontend, backend, PostgreSQL и Redis работают раздельно. У каждого сервиса своя зона ответственности и healthcheck. Если frontend сломан, backend/DB продолжают жить. Если backend недоступен, frontend может показать аккуратную ошибку вместо падения всей системы.

## Первый запуск

```bash
cd HackAlem_Team_Server
chmod +x scripts/*.sh
./scripts/init.sh
./scripts/start.sh
```

Открой:

```text
http://127.0.0.1:8080
```

Там будет Team Console со статусом сервисов.

## Режим разработки

```bash
./scripts/start-dev.sh
```

Backend работает с `--reload`, frontend — через Vite dev server.

## GUI управления

```bash
./scripts/start-tools.sh
```

Portainer:

```text
https://127.0.0.1:9443
```

Uptime Kuma:

```text
http://127.0.0.1:3001
```

Админ-панели специально привязаны только к localhost. Не публикуй Portainer напрямую в интернет.

## Командная работа

Создайте общий GitHub/GitLab-репозиторий. Каждый участник клонирует проект к себе и работает в своей ветке. Подробности — `TEAM_WORKFLOW.md`.

У каждого участника может быть собственный локальный Docker dev-stack. Общая integration-версия работает на твоём ноутбуке.

## Приватный доступ команды через Tailscale

На твоём ноутбуке:

```bash
sudo tailscale set --operator=$USER
tailscale serve --bg http://127.0.0.1:8080
```

После этого участники твоего tailnet смогут открыть HTTPS-адрес, который покажет Tailscale. Проброс портов на роутере не нужен.

## Публичный домен на время демонстрации

Если DNS домена управляется через Cloudflare:

1. Cloudflare Zero Trust → Networks → Tunnels.
2. Создай Tunnel.
3. Скопируй token в `.env` как `CF_TUNNEL_TOKEN=...`.
4. Создай Public Hostname, например `hack.domain.kz`.
5. Service укажи `http://gateway:80`.
6. Запусти:

```bash
./scripts/start-public.sh
```

Тогда публичный домен будет вести прямо на твой ноут через защищённый исходящий туннель. VPS и открытые входящие порты не нужны.

Если домен не находится на Cloudflare DNS, не переноси его вслепую — сначала выберем способ публикации отдельно.

## Проверка и логи

```bash
./scripts/doctor.sh
./scripts/status.sh
./scripts/logs.sh
```

Только backend:

```bash
./scripts/logs.sh backend
```

## Backup БД

```bash
./scripts/backup.sh
```

## Важное ограничение

Ноутбук теперь сервер. Если он выключен, спит или теряет интернет, общая версия недоступна. На хакатоне держи его на зарядке, отключи sleep от сети и по возможности используй стабильное подключение.
