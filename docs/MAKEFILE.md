# GraphFlow Makefile Reference

This document describes all available Makefile commands for developing and running GraphFlow.

## Quick Reference

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make install` | Install all packages in editable mode |
| `make dev-start` | Start full development environment |
| `make dev-stop` | Stop all services |
| `make status` | Show status of all services |
| `make test` | Run all tests |
| `make reset` | Full reset: stop, clean, reinstall, restart |

## Setup & Installation

### `make install`
Install all Python packages in editable mode (recommended for development).

```bash
make install
```

This installs:
- `graphflow-core` - Core library with step types and memory management
- `graphflow-plugins-ai` - AI plugin (LLM, Human Input steps)
- `graphflow-plugins-http` - HTTP plugin (GET, POST, PUT, PATCH, DELETE)
- `graphflow-plugin-example` - Example plugin for reference
- `graphflow-runtime` - FastAPI server for agent execution

**Why editable mode?** When packages are in editable mode, Python imports directly from your source code, so changes take effect immediately without reinstalling.

### `make dev-install`
Alias for `make install`.

### `make check-install`
Verify that all packages are installed in editable mode.

```bash
make check-install
```

Shows green checkmarks for packages in editable mode, red X for packages installed in site-packages.

### `make clean`
Remove all build artifacts, caches, and compiled files.

```bash
make clean
```

Cleans:
- Python: `__pycache__`, `*.egg-info`, `.pytest_cache`, `dist`, `build`, `*.pyc`
- Node: `.vite`, `dist` in builder and chat packages

### `make clean-install`
Clean everything and reinstall all packages in editable mode.

```bash
make clean-install
```

Equivalent to `make clean && make install`.

## Development Servers

### Starting Services

#### `make dev-start`
Start the full development environment (runtime + builder + chat UI).

```bash
make dev-start
```

This starts:
- Runtime server on http://localhost:8000
- Builder UI on http://localhost:3000
- Chat UI on http://localhost:3001

#### `make runtime-start`
Start only the GraphFlow runtime server (port 8000).

```bash
make runtime-start
```

The runtime provides:
- REST API for agent management
- Graph execution engine
- Debug/breakpoint support
- Plugin discovery

#### `make builder-start`
Start only the Builder UI dev server (port 3000).

```bash
make builder-start
```

The Builder UI provides:
- Visual drag-and-drop graph editor
- Step palette with plugin steps
- Memory schema management
- Runtime monitoring and debugging

#### `make chat-start`
Start only the Chat UI dev server (port 3001).

```bash
make chat-start
```

The Chat UI provides:
- Conversational interface for chat-enabled graphs
- Multi-graph and multi-session support
- Per-conversation debug mode

### Stopping Services

#### `make dev-stop`
Stop all services (runtime, builder, and chat UI).

```bash
make dev-stop
```

#### `make runtime-stop`
Stop only the runtime server.

```bash
make runtime-stop
```

#### `make builder-stop`
Stop only the Builder UI.

```bash
make builder-stop
```

#### `make chat-stop`
Stop only the Chat UI.

```bash
make chat-stop
```

### Viewing Logs

#### `make runtime-logs`
Show runtime server logs (follows/tails the log file).

```bash
make runtime-logs
```

Logs are stored in `/tmp/graphflow-runtime.log`.

#### `make builder-logs`
Show Builder UI logs.

```bash
make builder-logs
```

Logs are stored in `/tmp/graphflow-builder.log`.

#### `make chat-logs`
Show Chat UI logs.

```bash
make chat-logs
```

Logs are stored in `/tmp/graphflow-chat.log`.

## Status & Monitoring

### `make status`
Show the status of all services and package installations.

```bash
make status
```

Displays:
- Runtime status (port 8000)
- Builder status (port 3000)
- Chat UI status (port 3001)
- Package installation status (editable mode check)

## Testing

### `make test`
Run all tests using pytest.

```bash
make test
```

### `make test-core`
Run only core functionality tests.

```bash
make test-core
```

## Code Quality

### `make lint`
Run linting checks on the codebase.

```bash
make lint
```

Runs linting on:
- Builder UI (npm run lint)

### `make format`
Format code using black (Python) and prettier (TypeScript).

```bash
make format
```

Formats:
- Python packages with black
- Builder UI with prettier

## Building for Production

### `make builder-build`
Build the Builder UI for production deployment.

```bash
make builder-build
```

Output is placed in `packages/graph-builder/dist/`.

### `make chat-build`
Build the Chat UI for production deployment.

```bash
make chat-build
```

Output is placed in `packages/graph-chat/dist/`.

## Utilities

### `make reset`
Full reset: stop all services, clean build artifacts, reinstall packages, and restart services.

```bash
make reset
```

Equivalent to `make dev-stop && make clean && make install && make dev-start`.

Use this when you're having mysterious issues or after pulling significant changes.

### `make stats` / `make loc`
Show code statistics including lines of code by file type.

```bash
make stats
```

Displays:
- Lines of code for Python, TypeScript/JavaScript, Markdown, JSON, Jinja, CSS, Config files
- Percentage breakdown
- File counts by type

## Common Workflows

### Starting a Development Session

```bash
# Verify packages are in editable mode
make check-install

# If not in editable mode, reinstall
make install

# Start all services
make dev-start

# Verify everything is running
make status
```

### After Pulling Changes

```bash
# Clean and reinstall to pick up package changes
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

# View logs for specific service
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

# Stop services
make dev-stop
```

### When Things Go Wrong

```bash
# Nuclear option: clean everything and start fresh
make reset
```

## Port Reference

| Service | Port | URL |
|---------|------|-----|
| Runtime | 8000 | http://localhost:8000 |
| Builder UI | 3000 | http://localhost:3000 |
| Chat UI | 3001 | http://localhost:3001 |

## Log File Locations

| Service | Log File |
|---------|----------|
| Runtime | `/tmp/graphflow-runtime.log` |
| Builder UI | `/tmp/graphflow-builder.log` |
| Chat UI | `/tmp/graphflow-chat.log` |

## Troubleshooting

### Port Already in Use

If a port is already in use, the start commands will automatically kill the existing process. If that fails:

```bash
# Manually kill process on a port
lsof -ti:8000 | xargs kill -9  # Runtime
lsof -ti:3000 | xargs kill -9  # Builder
lsof -ti:3001 | xargs kill -9  # Chat UI
```

### Changes Not Taking Effect

```bash
# Verify editable mode
make check-install

# If not in editable mode, reinstall
make install

# Restart the runtime to pick up changes
make runtime-stop && make runtime-start
```

### Service Won't Start

Check the logs for error messages:

```bash
make runtime-logs   # or builder-logs, chat-logs
```

Common issues:
- Missing dependencies: Run `make install`
- Port conflict: Another process using the port
- Python environment: Make sure venv is activated

---

**See also:**
- [DEVELOPMENT.md](../DEVELOPMENT.md) - Development guide with workflows
- [README.md](../README.md) - Project overview and quick start
