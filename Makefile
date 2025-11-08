.PHONY: help install clean dev-install build test runtime-start runtime-stop builder-start builder-stop dev-start dev-stop status

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)GraphFlow Development Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Install all packages in editable mode (recommended for development)
	@echo "$(BLUE)Installing all packages in editable mode...$(NC)"
	pip install -e packages/graph-core
	pip install -e packages/graph-plugins-ai
	pip install -e packages/graph-plugins-http
	pip install -e packages/graph-plugin-example
	pip install -e packages/graph-runtime
	@echo "$(GREEN)✓ All packages installed in editable mode$(NC)"

dev-install: install ## Alias for install (install packages in editable mode)

check-install: ## Check if packages are installed in editable mode
	@echo "$(BLUE)Checking package installation...$(NC)"
	@pip show graphflow-core | grep Location | grep -q "site-packages" && echo "$(RED)✗ graphflow-core: NOT in editable mode (installed in site-packages)$(NC)" || echo "$(GREEN)✓ graphflow-core: in editable mode$(NC)"
	@pip show graphflow-plugins-ai | grep Location | grep -q "site-packages" && echo "$(RED)✗ graphflow-plugins-ai: NOT in editable mode$(NC)" || echo "$(GREEN)✓ graphflow-plugins-ai: in editable mode$(NC)"
	@pip show graphflow-plugins-http | grep Location | grep -q "site-packages" && echo "$(RED)✗ graphflow-plugins-http: NOT in editable mode$(NC)" || echo "$(GREEN)✓ graphflow-plugins-http: in editable mode$(NC)"
	@pip show graphflow-plugin-example | grep Location | grep -q "site-packages" && echo "$(RED)✗ graphflow-plugin-example: NOT in editable mode$(NC)" || echo "$(GREEN)✓ graphflow-plugin-example: in editable mode$(NC)"
	@pip show graphflow-runtime | grep Location | grep -q "site-packages" && echo "$(RED)✗ graphflow-runtime: NOT in editable mode$(NC)" || echo "$(GREEN)✓ graphflow-runtime: in editable mode$(NC)"

clean: ## Clean all build artifacts, caches, and compiled files
	@echo "$(BLUE)Cleaning build artifacts and caches...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	cd packages/graph-builder && rm -rf node_modules/.vite dist 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned all artifacts$(NC)"

clean-install: clean install ## Clean everything and reinstall packages

runtime-start: ## Start the GraphFlow runtime server
	@echo "$(BLUE)Starting GraphFlow runtime...$(NC)"
	@lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@sleep 1
	graphflow-runtime > /tmp/graphflow-runtime.log 2>&1 &
	@sleep 2
	@if lsof -ti:8000 > /dev/null; then \
		echo "$(GREEN)✓ Runtime started on http://localhost:8000$(NC)"; \
	else \
		echo "$(RED)✗ Runtime failed to start. Check /tmp/graphflow-runtime.log$(NC)"; \
		exit 1; \
	fi

runtime-stop: ## Stop the GraphFlow runtime server
	@echo "$(BLUE)Stopping GraphFlow runtime...$(NC)"
	@if lsof -ti:8000 > /dev/null 2>&1; then \
		lsof -ti:8000 | xargs kill -9 2>/dev/null; \
		echo "$(GREEN)✓ Runtime stopped$(NC)"; \
	else \
		echo "$(YELLOW)Runtime is not running$(NC)"; \
	fi

runtime-logs: ## Show runtime logs
	@tail -f /tmp/graphflow-runtime.log

builder-start: ## Start the builder UI dev server
	@echo "$(BLUE)Starting builder UI...$(NC)"
	@cd packages/graph-builder && npm run dev > /tmp/vite-dev.log 2>&1 &
	@sleep 3
	@if lsof -ti:3000 > /dev/null 2>&1 || lsof -ti:3001 > /dev/null 2>&1; then \
		PORT=$$(lsof -ti:3000 > /dev/null 2>&1 && echo "3000" || echo "3001"); \
		echo "$(GREEN)✓ Builder started on http://localhost:$$PORT$(NC)"; \
	else \
		echo "$(RED)✗ Builder failed to start. Check /tmp/vite-dev.log$(NC)"; \
		exit 1; \
	fi

builder-stop: ## Stop the builder UI dev server
	@echo "$(BLUE)Stopping builder UI...$(NC)"
	@if lsof -ti:3000 > /dev/null 2>&1; then \
		lsof -ti:3000 | xargs kill -9 2>/dev/null; \
		echo "$(GREEN)✓ Builder stopped (port 3000)$(NC)"; \
	elif lsof -ti:3001 > /dev/null 2>&1; then \
		lsof -ti:3001 | xargs kill -9 2>/dev/null; \
		echo "$(GREEN)✓ Builder stopped (port 3001)$(NC)"; \
	else \
		echo "$(YELLOW)Builder is not running$(NC)"; \
	fi

builder-logs: ## Show builder logs
	@tail -f /tmp/vite-dev.log

builder-build: ## Build the builder UI for production
	@echo "$(BLUE)Building builder UI...$(NC)"
	cd packages/graph-builder && npm run build
	@echo "$(GREEN)✓ Builder built$(NC)"

dev-start: runtime-start builder-start ## Start both runtime and builder (full dev environment)

dev-stop: runtime-stop builder-stop ## Stop both runtime and builder

status: ## Show status of runtime and builder
	@echo "$(BLUE)GraphFlow Status:$(NC)"
	@echo ""
	@echo "Runtime (port 8000):"
	@if lsof -ti:8000 > /dev/null 2>&1; then \
		echo "  $(GREEN)✓ Running$(NC) (http://localhost:8000)"; \
	else \
		echo "  $(RED)✗ Not running$(NC)"; \
	fi
	@echo ""
	@echo "Builder (port 3000/3001):"
	@if lsof -ti:3000 > /dev/null 2>&1; then \
		echo "  $(GREEN)✓ Running$(NC) (http://localhost:3000)"; \
	elif lsof -ti:3001 > /dev/null 2>&1; then \
		echo "  $(GREEN)✓ Running$(NC) (http://localhost:3001)"; \
	else \
		echo "  $(RED)✗ Not running$(NC)"; \
	fi
	@echo ""
	@echo "Package installation:"
	@make check-install 2>/dev/null

test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	pytest tests/ -v
	@echo "$(GREEN)✓ Tests complete$(NC)"

test-core: ## Run core functionality tests only
	@echo "$(BLUE)Running core tests...$(NC)"
	pytest tests/test_core_functionality.py -v

lint: ## Run linting checks
	@echo "$(BLUE)Running linting...$(NC)"
	cd packages/graph-builder && npm run lint || true
	@echo "$(GREEN)✓ Linting complete$(NC)"

format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	black packages/graph-core packages/graph-runtime packages/graph-plugins-*
	cd packages/graph-builder && npm run format || true
	@echo "$(GREEN)✓ Code formatted$(NC)"

reset: dev-stop clean install dev-start ## Full reset: stop everything, clean, reinstall, restart

.DEFAULT_GOAL := help
