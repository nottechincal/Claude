.PHONY: dev prod setup migrate logs shell clean

# Development with ngrok
dev:
	docker compose --profile dev up --build

# Production
prod:
	docker compose up -d --build

# Setup (first time)
setup:
	cp -n .env.example .env || true
	docker compose up -d postgres redis
	sleep 3
	docker compose run --rm app alembic upgrade head

# Run migrations
migrate:
	docker compose run --rm app alembic upgrade head

# View logs
logs:
	docker compose logs -f app

# Shell into app
shell:
	docker compose exec app bash

# Clean everything
clean:
	docker compose down -v

# Local dev without Docker
local-dev:
	pip install -r requirements.txt
	uvicorn app.main:app --reload --port 8000

# Generate new migration
migration:
	docker compose run --rm app alembic revision --autogenerate -m "$(MSG)"
