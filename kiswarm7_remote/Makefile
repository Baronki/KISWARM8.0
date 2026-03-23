# =============================================================================
# KISWARM6.0 Makefile
# =============================================================================
# Convenient commands for KISWARM6.0 management
#
# Usage: make <target>
#
# Author: Baron Marco Paolo Ialongo
# Version: 6.0.0
# =============================================================================

.PHONY: all install start stop restart health deploy docker-build docker-up docker-down docker-logs clean help

# Default target
all: help

# =============================================================================
# Development Commands
# =============================================================================

## Install dependencies
install:
	@echo "Installing KISWARM6.0 dependencies..."
	@./scripts/install.sh

## Start all services
start:
	@echo "Starting KISWARM6.0 services..."
	@./scripts/start.sh

## Stop all services
stop:
	@echo "Stopping KISWARM6.0 services..."
	@./scripts/stop.sh

## Restart all services
restart: stop start
	@echo "KISWARM6.0 services restarted."

## Check health of all services
health:
	@./scripts/health-check.sh

## Production deployment
deploy:
	@echo "Deploying KISWARM6.0 for production..."
	@./scripts/deploy.sh

# =============================================================================
# Docker Commands
# =============================================================================

## Build Docker images
docker-build:
	@echo "Building Docker images..."
	@docker-compose build

## Start Docker containers
docker-up:
	@echo "Starting Docker containers..."
	@docker-compose up -d

## Stop Docker containers
docker-down:
	@echo "Stopping Docker containers..."
	@docker-compose down

## View Docker logs
docker-logs:
	@docker-compose logs -f

## Start full Docker stack (with Redis and Nginx)
docker-full:
	@echo "Starting full Docker stack..."
	@docker-compose --profile full up -d

## Stop all Docker resources
docker-clean:
	@echo "Cleaning Docker resources..."
	@docker-compose down -v --remove-orphans

# =============================================================================
# Database Commands
# =============================================================================

## Run database migrations
db-migrate:
	@echo "Running database migrations..."
	@cd frontend && pnpm db:push

## Reset database
db-reset:
	@echo "Resetting database..."
	@cd frontend && pnpm drizzle-kit drop && pnpm db:push

# =============================================================================
# Development Commands
# =============================================================================

## Run backend in development mode
dev-backend:
	@echo "Starting backend in development mode..."
	@cd backend && source ../.venv/bin/activate && python run.py

## Run frontend in development mode
dev-frontend:
	@echo "Starting frontend in development mode..."
	@cd frontend && pnpm dev

## Run tests
test:
	@echo "Running tests..."
	@cd backend && source ../.venv/bin/activate && pytest python/ -v
	@cd frontend && pnpm test

## Run linters
lint:
	@echo "Running linters..."
	@cd backend && source ../.venv/bin/activate && flake8 python/
	@cd frontend && pnpm check

# =============================================================================
# Cleanup
# =============================================================================

## Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf frontend/dist
	@rm -rf backend/__pycache__
	@rm -rf backend/python/__pycache__
	@rm -rf backend/python/*/__pycache__
	@rm -rf .pytest_cache
	@rm -rf .mypy_cache
	@rm -rf logs/*.log
	@rm -rf tmp/*

# =============================================================================
# Help
# =============================================================================

## Show this help message
help:
	@echo "KISWARM6.0 - KI-natives Finanzprotokoll"
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@sed -n 's/^## //p' $(MAKEFILE_LIST) | column -t -s ':'
