# Architecture

```text
                           TEAM
             frontend / web / backend+AI
                         |
                         v
                 GitHub or GitLab
              feature -> dev -> main
                         |
                         v
                 YOUR THUNDEROBOT

 optional public domain                    private team access
 Cloudflare Tunnel                         Tailscale
          |                                    |
          +----------------+-------------------+
                           v
                     Caddy Gateway
                    /             \
             React Frontend     FastAPI Backend
                                   /       \
                            PostgreSQL     Redis

 Local-only admin:
 - Portainer :9443
 - Uptime Kuma :3001
```

## Isolation

- `frontend` and `backend` are separate containers.
- database network is marked `internal`.
- PostgreSQL/Redis have no host ports.
- admin interfaces are bound to `127.0.0.1` only.
- public Cloudflare Tunnel reaches only the gateway network.
- healthchecks allow one failed component to be identified separately.
- CI has independent frontend/backend jobs.
