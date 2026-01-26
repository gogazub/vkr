.PHONY: help build up down restart logs test test-cov clean shell db-shell health start

# Default target
help:
	@echo "Validation Microservice - Makefile Commands"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make build          - Build Docker images"
	@echo "  make up              - Start all services (PostgreSQL + API)"
	@echo "  make up-d           - Start all services in detached mode"
	@echo "  make down           - Stop all services"
	@echo "  make restart        - Restart all services"
	@echo "  make logs           - View logs from all services"
	@echo "  make logs-api       - View API service logs"
	@echo "  make logs-db        - View PostgreSQL logs"
	@echo ""
	@echo "Testing Commands:"
	@echo "  make test           - Run tests in Docker container"
	@echo "  make test-cov       - Run tests with coverage in Docker container"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make clean          - Clean up temporary files and containers"
	@echo "  make shell          - Open shell in API container"
	@echo "  make db-shell       - Open PostgreSQL shell"
	@echo "  make health         - Check service health"
	@echo "  make start          - Quick start (build and run)"

# Docker commands
build:
	docker compose build

up:
	docker compose up

up-d:
	docker compose up -d

down:
	docker compose down

restart: down up-d

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-db:
	docker compose logs -f postgres

# Testing commands (only in Docker)
test:
	docker compose exec api pytest

test-cov:
	docker compose exec api pytest --cov=app --cov-report=term-missing --cov-report=html

# Utility commands
clean:
	docker compose down -v
	docker system prune -f
	@echo "Cleanup complete!"

shell:
	docker compose exec api /bin/bash

db-shell:
	docker compose exec postgres psql -U postgres -d validation_db

health:
	@echo "Checking service health..."
	@curl -s http://localhost:8000/health | python -m json.tool || echo "Service is not running. Start it with: make start"

# Quick start (build and run)
start: build up-d
	@echo "Services started! API available at http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
