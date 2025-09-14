
# Crypto Analytics Dashboard — Project Scaffold

This repository scaffold is generated directly from your **PROJECT_BLUEPRINT** and companion docs.
It wires up a **local-first** stack with strict 127.0.0.1 binding, Compose profiles, health checks,
and CI-friendly structure. See `/docs` for the authoritative specs.

## Quickstart

```bash
# 0) prerequisites: Docker & Docker Compose, Node 20+, Python 3.12+
# 1) copy env
cp .env.example .env

# 2) start core services (frontend, api, redis)
docker compose up

# 3) optional: add worker and observability
docker compose --profile worker up -d
docker compose --profile ops up -d
```

## Profiles

- **default**: `frontend`, `api`, `redis`
- **worker**: `worker`
- **ops**: `otel-collector`

## Notes

- All services bind to **127.0.0.1** only.
- No secrets are checked in; use `.env`.
- See `Makefile` for `check`, `test`, `backup`, `backup.verify`, `restore` targets.
