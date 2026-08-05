PYTHON ?= python
NPM ?= npm
COMPOSE = docker compose -f infra/local/docker-compose.yml

.PHONY: db-up db-down install migrate seed backend-dev frontend-dev test check

db-up:
	$(COMPOSE) up -d

db-down:
	$(COMPOSE) down

install:
	$(PYTHON) -m pip install -e "./backend[dev]"
	cd frontend && $(NPM) install

migrate:
	cd backend && $(PYTHON) -m alembic upgrade head

seed:
	$(PYTHON) scripts/seed_demo_data.py

backend-dev:
	cd backend && $(PYTHON) -m uvicorn app.main:app --reload --port 8000

frontend-dev:
	cd frontend && $(NPM) run dev

test:
	cd backend && $(PYTHON) -m pytest
	cd frontend && $(NPM) test -- --run

check:
	cd backend && $(PYTHON) -m ruff format --no-cache --check app tests && $(PYTHON) -m ruff check --no-cache app tests && $(PYTHON) -m mypy app && $(PYTHON) -m pytest
	cd frontend && $(NPM) run lint && $(NPM) run typecheck && $(NPM) test -- --run && $(NPM) run build
