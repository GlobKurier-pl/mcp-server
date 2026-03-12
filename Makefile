# ============================================
# GlobKurier MCP Server - Makefile
# ============================================
# Convenient commands for Docker operations

.PHONY: help build up down restart logs shell clean test dev-up dev-down dev-logs health status rebuild

# Default target
.DEFAULT_GOAL := help

# Variables
DOCKER_COMPOSE := docker-compose
DOCKER_COMPOSE_DEV := docker-compose -f docker-compose.yml -f docker-compose.dev.yml
CONTAINER_NAME := globkurier-mcp-server
IMAGE_NAME := globkurier-mcp

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

##@ General

help: ## Display this help message
	@echo "$(GREEN)GlobKurier MCP Server - Docker Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(YELLOW)<target>$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Docker Production

build: ## Build Docker image
	@echo "$(GREEN)Building Docker image...$(NC)"
	$(DOCKER_COMPOSE) build

up: ## Start containers in detached mode
	@echo "$(GREEN)Starting containers...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)Containers started. Use 'make logs' to see output$(NC)"

down: ## Stop and remove containers
	@echo "$(YELLOW)Stopping containers...$(NC)"
	$(DOCKER_COMPOSE) down

restart: down up ## Restart containers

rebuild: ## Rebuild and restart containers
	@echo "$(GREEN)Rebuilding and restarting...$(NC)"
	$(DOCKER_COMPOSE) up -d --build

logs: ## Show container logs (follow mode)
	$(DOCKER_COMPOSE) logs -f

logs-tail: ## Show last 100 lines of logs
	$(DOCKER_COMPOSE) logs --tail=100

##@ Docker Development

dev-up: ## Start development environment with hot-reload
	@echo "$(GREEN)Starting development environment...$(NC)"
	$(DOCKER_COMPOSE_DEV) up -d
	@echo "$(GREEN)Dev environment started with code hot-reload$(NC)"

dev-down: ## Stop development environment
	@echo "$(YELLOW)Stopping development environment...$(NC)"
	$(DOCKER_COMPOSE_DEV) down

dev-logs: ## Show development container logs
	$(DOCKER_COMPOSE_DEV) logs -f

dev-restart: dev-down dev-up ## Restart development environment

##@ Container Management

shell: ## Open bash shell in running container
	@echo "$(GREEN)Opening shell in container...$(NC)"
	docker exec -it $(CONTAINER_NAME) /bin/bash

shell-root: ## Open bash shell as root user
	@echo "$(YELLOW)Opening root shell in container...$(NC)"
	docker exec -it -u root $(CONTAINER_NAME) /bin/bash

health: ## Check container health status
	@echo "$(GREEN)Health Status:$(NC)"
	@docker inspect $(CONTAINER_NAME) --format='{{.State.Health.Status}}' 2>/dev/null && \
	 docker inspect $(CONTAINER_NAME) --format='Last check: {{.State.Health.Log}}' | head -n 5 || \
	 echo "$(RED)Container not running or no health check configured$(NC)"

test-connection: ## Test TCP connection to MCP server
	@echo "$(GREEN)Testing connection to MCP server...$(NC)"
	@python3 -c "import socket; s=socket.socket(); s.settimeout(5); s.connect(('127.0.0.1', 9000)); s.close(); print('✓ Connection successful')" || \
	 echo "$(RED)✗ Connection failed$(NC)"

status: ## Show container status
	@echo "$(GREEN)Container Status:$(NC)"
	@docker ps -a --filter "name=$(CONTAINER_NAME)" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

ps: ## List all containers
	$(DOCKER_COMPOSE) ps

##@ Cleanup

clean: down ## Stop containers and remove volumes
	@echo "$(RED)Removing volumes...$(NC)"
	$(DOCKER_COMPOSE) down -v

clean-all: ## Remove containers, volumes, and images
	@echo "$(RED)Removing everything...$(NC)"
	$(DOCKER_COMPOSE) down -v --rmi all

prune: ## Remove unused Docker resources
	@echo "$(YELLOW)Pruning Docker system...$(NC)"
	docker system prune -f
	docker volume prune -f

##@ Testing & Development

test: ## Run tests in container
	@echo "$(GREEN)Running tests...$(NC)"
	docker exec $(CONTAINER_NAME) pytest

test-cov: ## Run tests with coverage
	@echo "$(GREEN)Running tests with coverage...$(NC)"
	docker exec $(CONTAINER_NAME) pytest --cov=globkurier_mcp

lint: ## Run linter in container
	@echo "$(GREEN)Running linter...$(NC)"
	docker exec $(CONTAINER_NAME) ruff check globkurier_mcp

type-check: ## Run type checker in container
	@echo "$(GREEN)Running type checker...$(NC)"
	docker exec $(CONTAINER_NAME) mypy globkurier_mcp

##@ Local Development (without Docker)

local-install: ## Install dependencies locally with uv
	@echo "$(GREEN)Installing dependencies...$(NC)"
	uv sync

local-run: ## Run server locally
	@echo "$(GREEN)Running server locally...$(NC)"
	python -m globkurier_mcp.main

local-test: ## Run tests locally
	@echo "$(GREEN)Running tests locally...$(NC)"
	pytest

local-test-cov: ## Run tests with coverage locally
	@echo "$(GREEN)Running tests with coverage locally...$(NC)"
	pytest --cov=globkurier_mcp

##@ Monitoring

watch-logs: ## Watch logs with grep filter (usage: make watch-logs FILTER=ERROR)
	$(DOCKER_COMPOSE) logs -f | grep --line-buffered "$(FILTER)"

inspect: ## Show detailed container information
	@docker inspect $(CONTAINER_NAME)

stats: ## Show real-time container resource usage
	@docker stats $(CONTAINER_NAME)

ports: ## Show exposed ports
	@docker port $(CONTAINER_NAME)