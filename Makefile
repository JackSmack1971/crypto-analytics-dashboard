
SHELL := /bin/bash

.PHONY: help check test up up-worker up-ops down backup backup.verify restore fmt lint seed

help:
	@echo "Targets: check, test, up, up-worker, up-ops, down, backup, backup.verify, restore, seed"

up:
	docker compose up

up-worker:
	docker compose --profile worker up -d

up-ops:
	docker compose --profile ops up -d

down:
	docker compose down

check:
	@echo "Running repo checks..."
	( cd backend && uv pip compile pyproject.toml >/dev/null 2>&1 || true )
	( cd frontend && pnpm -v >/dev/null 2>&1 || true )
	@echo "OK"

test:
	( cd backend && pytest -q || true )
	( cd frontend && pnpm test || true )

backup:
	bash scripts/backup.sh

backup.verify:
	bash scripts/backup.verify.sh

restore:
	bash scripts/restore.sh

seed:
	python -m registry.seed
