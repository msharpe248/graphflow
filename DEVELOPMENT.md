# GraphFlow Development Guide

## Quick Start

```bash
# Install all packages in editable mode
make install

# Start development environment (runtime + builder + chat UI)
make dev-start

# Check status
make status
```

## Makefile Commands

### Setup & Installation

- `make install` - Install all packages in **editable mode** (recommended for development)
- `make check-install` - Check if packages are installed in editable mode
- `make clean` - Clean all build artifacts, caches, and compiled files
- `make clean-install` - Clean everything and reinstall packages

### Development Servers

- `make runtime-start` - Start GraphFlow runtime server (port 8000)
- `make runtime-stop` - Stop GraphFlow runtime server
- `make runtime-logs` - Show runtime logs

- `make builder-start` - Start builder UI dev server (port 3000)
- `make builder-stop` - Stop builder UI dev server
- `make builder-logs` - Show builder logs

- `make chat-start` - Start chat UI dev server (port 3001)
- `make chat-stop` - Stop chat UI dev server
- `make chat-logs` - Show chat UI logs

- `make dev-start` - Start runtime, builder, and chat UI (full dev environment)
- `make dev-stop` - Stop runtime, builder, and chat UI

### Status & Testing

- `make status` - Show status of all services and package installations
- `make test` - Run all tests
- `make test-core` - Run core functionality tests only

### Utilities

- `make lint` - Run linting checks
- `make format` - Format code (Python with black, TypeScript with prettier)
- `make builder-build` - Build builder UI for production
- `make chat-build` - Build chat UI for production
- `make reset` - **Full reset**: stop everything, clean, reinstall, restart
- `make stats` / `make loc` - Show code statistics (lines of code by file type)

### Help

- `make help` - Show all available commands

## Common Workflows

### Starting a Development Session

```bash
# Make sure packages are in editable mode
make check-install

# If not in editable mode, reinstall
make install

# Start runtime, builder, and chat UI
make dev-start

# Check everything is running
make status
```

### After Pulling Changes

```bash
# Clean and reinstall to pick up any package changes
make clean-install

# Restart services
make dev-start
```

### Debugging Issues

```bash
# Check if packages are in editable mode
make check-install

# Check service status
make status

# View logs
make runtime-logs
make builder-logs
make chat-logs
```

### Before Committing

```bash
# Format code
make format

# Run tests
make test

# Stop services to avoid conflicts
make dev-stop
```

## Important Notes

### Editable Mode

**Always use editable mode (`make install`) for development!**

When packages are installed normally (`pip install packages/graph-core`), they're copied to `site-packages` and your code changes won't take effect until you reinstall.

With editable mode (`pip install -e packages/graph-core`), Python imports directly from your source code, so changes take effect immediately.

Use `make check-install` regularly to verify all packages are in editable mode.

### Port Conflicts

If ports 8000, 3000, or 3001 are already in use:

```bash
# Stop GraphFlow services
make dev-stop

# Find and kill conflicting processes
lsof -ti:8000 | xargs kill -9  # Runtime
lsof -ti:3000 | xargs kill -9  # Builder
lsof -ti:3001 | xargs kill -9  # Chat UI
```

### Clean Slate

If you're having mysterious issues:

```bash
# Nuclear option: clean everything and start fresh
make reset
```

This will:
1. Stop all services
2. Clean all caches and build artifacts
3. Reinstall all packages in editable mode
4. Restart all services

## Architecture

```
graphflow/
├── packages/
│   ├── graph-core/          # Core graph execution engine
│   ├── graph-runtime/       # Multi-graph runtime server
│   ├── graph-builder/       # React UI for building graphs
│   ├── graph-chat/          # React UI for chat interactions
│   ├── graph-plugins-ai/    # AI plugin (LLM, Human Input)
│   ├── graph-plugins-http/  # HTTP plugin (requests, parsing)
│   └── graph-plugin-example/# Example plugin
├── tests/                   # Test suite
└── Makefile                 # Development commands
```

## Plugin Development

When developing plugins:

1. **Always install in editable mode**: `make install`
2. **Test changes**: Make code changes, they take effect immediately
3. **Restart runtime if needed**: `make runtime-stop && make runtime-start`
4. **Check plugin loads**: Visit http://localhost:8000/api/v1/plugins

## Troubleshooting

### "Changes not taking effect"

→ Run `make check-install` to verify editable mode
→ If not in editable mode, run `make install`

### "Runtime won't start"

→ Check logs: `make runtime-logs`
→ Check port: `lsof -ti:8000`
→ Try: `make runtime-stop && make runtime-start`

### "Builder shows old data"

→ Hard refresh browser (Cmd+Shift+R)
→ Check API response: `curl http://localhost:8000/api/v1/steps`
→ Restart runtime: `make runtime-stop && make runtime-start`

### "Chat UI won't start"

→ Check logs: `make chat-logs`
→ Check port: `lsof -ti:3001`
→ Try: `make chat-stop && make chat-start`
→ Make sure npm dependencies are installed: `cd packages/graph-chat && npm install`

### "Tests failing mysteriously"

→ Clean and reinstall: `make clean-install`
→ Check Python environment: `which python` should be in venv
→ Verify package installation: `make check-install`
