.PHONY: help install clean dev-install build test runtime-start runtime-stop builder-start builder-stop chat-start chat-stop dev-start dev-stop status stats loc

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
	cd packages/graph-chat && rm -rf node_modules/.vite dist 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned all artifacts$(NC)"

clean-install: clean install ## Clean everything and reinstall packages

runtime-start: ## Start the GraphFlow runtime server
	@echo "$(BLUE)Starting GraphFlow runtime...$(NC)"
	@lsof -ti:8000 -sTCP:LISTEN | xargs kill -9 2>/dev/null || true
	@sleep 1
	graphflow-runtime > /tmp/graphflow-runtime.log 2>&1 &
	@sleep 2
	@if lsof -ti:8000 -sTCP:LISTEN > /dev/null; then \
		echo "$(GREEN)✓ Runtime started on http://localhost:8000$(NC)"; \
	else \
		echo "$(RED)✗ Runtime failed to start. Check /tmp/graphflow-runtime.log$(NC)"; \
		exit 1; \
	fi

runtime-stop: ## Stop the GraphFlow runtime server
	@echo "$(BLUE)Stopping GraphFlow runtime...$(NC)"
	@if lsof -ti:8000 -sTCP:LISTEN > /dev/null 2>&1; then \
		lsof -ti:8000 -sTCP:LISTEN | xargs kill -9 2>/dev/null; \
		echo "$(GREEN)✓ Runtime stopped$(NC)"; \
	else \
		echo "$(YELLOW)Runtime is not running$(NC)"; \
	fi

runtime-logs: ## Show runtime logs
	@tail -f /tmp/graphflow-runtime.log

builder-start: ## Start the builder UI dev server (port 3000)
	@echo "$(BLUE)Starting builder UI...$(NC)"
	@lsof -ti:3000 -sTCP:LISTEN | xargs kill -9 2>/dev/null || true
	@sleep 1
	@cd packages/graph-builder && npm run dev > /tmp/graphflow-builder.log 2>&1 &
	@sleep 3
	@if lsof -ti:3000 -sTCP:LISTEN > /dev/null 2>&1; then \
		echo "$(GREEN)✓ Builder started on http://localhost:3000$(NC)"; \
	else \
		echo "$(RED)✗ Builder failed to start. Check /tmp/graphflow-builder.log$(NC)"; \
		exit 1; \
	fi

builder-stop: ## Stop the builder UI dev server
	@echo "$(BLUE)Stopping builder UI...$(NC)"
	@if lsof -ti:3000 -sTCP:LISTEN > /dev/null 2>&1; then \
		lsof -ti:3000 -sTCP:LISTEN | xargs kill -9 2>/dev/null; \
		echo "$(GREEN)✓ Builder stopped$(NC)"; \
	else \
		echo "$(YELLOW)Builder is not running$(NC)"; \
	fi

builder-logs: ## Show builder logs
	@tail -f /tmp/graphflow-builder.log

chat-start: ## Start the chat UI dev server (port 3001)
	@echo "$(BLUE)Starting chat UI...$(NC)"
	@lsof -ti:3001 -sTCP:LISTEN | xargs kill -9 2>/dev/null || true
	@sleep 1
	@cd packages/graph-chat && npm run dev > /tmp/graphflow-chat.log 2>&1 &
	@sleep 3
	@if lsof -ti:3001 -sTCP:LISTEN > /dev/null 2>&1; then \
		echo "$(GREEN)✓ Chat UI started on http://localhost:3001$(NC)"; \
	else \
		echo "$(RED)✗ Chat UI failed to start. Check /tmp/graphflow-chat.log$(NC)"; \
		exit 1; \
	fi

chat-stop: ## Stop the chat UI dev server
	@echo "$(BLUE)Stopping chat UI...$(NC)"
	@if lsof -ti:3001 -sTCP:LISTEN > /dev/null 2>&1; then \
		lsof -ti:3001 -sTCP:LISTEN | xargs kill -9 2>/dev/null; \
		echo "$(GREEN)✓ Chat UI stopped$(NC)"; \
	else \
		echo "$(YELLOW)Chat UI is not running$(NC)"; \
	fi

chat-logs: ## Show chat UI logs
	@tail -f /tmp/graphflow-chat.log

chat-build: ## Build the chat UI for production
	@echo "$(BLUE)Building chat UI...$(NC)"
	cd packages/graph-chat && npm run build
	@echo "$(GREEN)✓ Chat UI built$(NC)"

builder-build: ## Build the builder UI for production
	@echo "$(BLUE)Building builder UI...$(NC)"
	cd packages/graph-builder && npm run build
	@echo "$(GREEN)✓ Builder built$(NC)"

dev-start: runtime-start builder-start chat-start ## Start runtime, builder, and chat UI (full dev environment)

dev-stop: runtime-stop builder-stop chat-stop ## Stop runtime, builder, and chat UI

status: ## Show status of runtime, builder, and chat UI
	@echo "$(BLUE)GraphFlow Status:$(NC)"
	@echo ""
	@echo "Runtime (port 8000):"
	@if lsof -ti:8000 -sTCP:LISTEN > /dev/null 2>&1; then \
		echo "  $(GREEN)✓ Running$(NC) (http://localhost:8000)"; \
	else \
		echo "  $(RED)✗ Not running$(NC)"; \
	fi
	@echo ""
	@echo "Builder (port 3000):"
	@if lsof -ti:3000 -sTCP:LISTEN > /dev/null 2>&1; then \
		echo "  $(GREEN)✓ Running$(NC) (http://localhost:3000)"; \
	else \
		echo "  $(RED)✗ Not running$(NC)"; \
	fi
	@echo ""
	@echo "Chat UI (port 3001):"
	@if lsof -ti:3001 -sTCP:LISTEN > /dev/null 2>&1; then \
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

stats: ## Show code statistics (lines of code by file type)
	@echo "$(BLUE)╔═══════════════════════════════════════════════╗$(NC)"
	@echo "$(BLUE)║    GraphFlow Code Statistics                 ║$(NC)"
	@echo "$(BLUE)╚═══════════════════════════════════════════════╝$(NC)"
	@echo ""
	@PY_LINES=$$(find . -type f -name "*.py" ! -path "*/node_modules/*" ! -path "*/.venv/*" ! -path "*/venv/*" ! -path "*/__pycache__/*" ! -path "*/.pytest_cache/*" ! -path "*/dist/*" ! -path "*/build/*" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $$1}'); \
	TS_LINES=$$(find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) ! -path "*/node_modules/*" ! -path "*/dist/*" ! -path "*/build/*" ! -path "*/.next/*" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $$1}'); \
	MD_LINES=$$(find . -type f -name "*.md" ! -path "*/node_modules/*" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $$1}'); \
	JSON_LINES=$$(find . -type f -name "*.json" ! -path "*/node_modules/*" ! -path "*/dist/*" ! -path "*/build/*" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $$1}'); \
	JINJA_LINES=$$(find . -type f -name "*.jinja" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $$1}'); \
	CSS_LINES=$$(find . -type f -name "*.css" ! -path "*/node_modules/*" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $$1}'); \
	CFG_LINES=$$(find . -type f \( -name "*.toml" -o -name "*.yaml" -o -name "*.yml" \) ! -path "*/node_modules/*" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $$1}'); \
	TOTAL=$$((PY_LINES + TS_LINES + MD_LINES + JSON_LINES + JINJA_LINES + CSS_LINES + CFG_LINES)); \
	PY_PCT=$$((PY_LINES * 100 / TOTAL)); \
	TS_PCT=$$((TS_LINES * 100 / TOTAL)); \
	MD_PCT=$$((MD_LINES * 100 / TOTAL)); \
	printf "  $(GREEN)%-35s$(NC) %7s  (%2d%%)\n" "Python (.py)" "$$(printf "%'d" $$PY_LINES)" $$PY_PCT; \
	printf "  $(BLUE)%-35s$(NC) %7s  (%2d%%)\n" "TypeScript/JavaScript (.ts/.tsx/.js/.jsx)" "$$(printf "%'d" $$TS_LINES)" $$TS_PCT; \
	printf "  $(YELLOW)%-35s$(NC) %7s  (%2d%%)\n" "Markdown (.md)" "$$(printf "%'d" $$MD_LINES)" $$MD_PCT; \
	printf "  %-35s %7s\n" "JSON (.json)" "$$(printf "%'d" $$JSON_LINES)"; \
	printf "  %-35s %7s\n" "Jinja Templates (.jinja)" "$$(printf "%'d" $$JINJA_LINES)"; \
	printf "  %-35s %7s\n" "CSS (.css)" "$$(printf "%'d" $$CSS_LINES)"; \
	printf "  %-35s %7s\n" "Config (.toml/.yaml/.yml)" "$$(printf "%'d" $$CFG_LINES)"; \
	echo "  $(BLUE)─────────────────────────────────────────────$(NC)"; \
	printf "  $(GREEN)%-35s %7s$(NC)\n" "TOTAL" "$$(printf "%'d" $$TOTAL)"; \
	echo ""; \
	PY_FILES=$$(find . -type f -name "*.py" ! -path "*/node_modules/*" ! -path "*/.venv/*" ! -path "*/venv/*" ! -path "*/__pycache__/*" ! -path "*/.pytest_cache/*" ! -path "*/dist/*" ! -path "*/build/*" | wc -l | xargs); \
	TS_FILES=$$(find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" \) ! -path "*/node_modules/*" ! -path "*/dist/*" ! -path "*/build/*" ! -path "*/.next/*" | wc -l | xargs); \
	MD_FILES=$$(find . -type f -name "*.md" ! -path "*/node_modules/*" | wc -l | xargs); \
	JSON_FILES=$$(find . -type f -name "*.json" ! -path "*/node_modules/*" ! -path "*/dist/*" ! -path "*/build/*" | wc -l | xargs); \
	echo "$(BLUE)File Counts:$(NC)"; \
	printf "  Python files:         %4s\n" "$$PY_FILES"; \
	printf "  TS/JS files:          %4s\n" "$$TS_FILES"; \
	printf "  Markdown files:       %4s\n" "$$MD_FILES"; \
	printf "  JSON files:           %4s\n" "$$JSON_FILES"

loc: stats ## Alias for stats (show lines of code)

.DEFAULT_GOAL := help
