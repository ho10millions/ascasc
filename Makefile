.PHONY: dev stop build migrate test lint

dev:
	docker-compose up -d

stop:
	docker-compose down

build:
	docker-compose build

migrate:
	docker-compose exec backend alembic upgrade head

test:
	docker-compose exec backend pytest -v

lint:
	docker-compose exec backend ruff check app/

logs:
	docker-compose logs -f

logs-scraper:
	docker-compose logs -f scraper-worker

shell-backend:
	docker-compose exec backend bash

shell-db:
	docker-compose exec postgres psql -U scrooge -d scrooge_db
