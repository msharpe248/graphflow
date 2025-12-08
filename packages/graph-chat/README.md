# GraphFlow Chat UI

Conversational interface for interacting with chat-enabled GraphFlow graphs.

## Overview

The Chat UI provides a standalone application for having conversations with AI agents built in GraphFlow. It connects to the GraphFlow Runtime API and supports multi-graph, multi-session interactions.

## Requirements

### Graph Eligibility

A graph must have both of these in its memory schema to be chat-eligible:
- **Input**: `query` (string) - The user's message
- **Output**: `query_response` (string) - The agent's response

Example memory schema:
```json
{
  "memory": {
    "inputs": {
      "query": { "type": "string", "required": true }
    },
    "outputs": {
      "query_response": { "type": "string" }
    }
  }
}
```

## Features

- **Multi-Graph Support**: Have multiple graphs active in the sidebar simultaneously
- **Multi-Session**: Create multiple conversations per graph with independent history
- **Debug Mode**: Per-conversation toggle - when enabled, runs appear in Runtime UI for debugging
- **Real-time Responses**: Poll-based message delivery with typing indicators
- **Session Persistence**: Uses session IDs for multi-turn conversation context

## Getting Started

### Using Makefile (Recommended)

```bash
# Start all services (runtime, builder, chat)
make dev-start

# Or start just the chat UI
make chat-start

# Check status
make status

# Stop chat UI
make chat-stop
```

### Manual Setup

```bash
cd packages/graph-chat
npm install
npm run dev
```

Visit http://localhost:3001

## Usage

### Adding Graphs

1. Click the "+" button in the sidebar
2. Choose from:
   - **From Runtime**: Select an eligible agent already loaded in runtime
   - **From File**: Upload a graph JSON file (creates agent automatically)

### Starting a Conversation

1. Select a graph from the sidebar
2. Click "New Conversation"
3. Type your message and press Enter or click Send

### Debug Mode

Toggle debug mode per conversation using the bug icon in the chat header:
- **Enabled**: Runs appear in Runtime UI for step-through debugging
- **Disabled**: Runs execute without debug visibility

### Cross-App Navigation

Access Chat UI from other GraphFlow apps:
- **From Builder**: Click the green "Chat" button in the toolbar (visible when graph is eligible)
- **From Runtime**: Click the chat icon next to eligible agents in the agents list
- **Direct URL**: `http://localhost:3001?agentId={agent_id}`

## Architecture

```
src/
├── components/
│   ├── chat/           # Message display and input
│   ├── layout/         # Main layout and header
│   ├── modals/         # Add graph and settings modals
│   └── sidebar/        # Graph and conversation lists
├── hooks/
│   ├── useChat.ts      # Message sending and polling
│   └── useRuntime.ts   # Runtime API integration
├── stores/
│   ├── chatStore.ts    # Conversations, messages, graphs (Zustand)
│   └── settingsStore.ts # Runtime connection settings
├── services/
│   └── runtime.ts      # API client
└── types/
    └── chat.ts         # Types and eligibility check
```

## API Integration

The Chat UI uses the same Runtime API as the Builder:

- `GET /agents` - List available agents
- `GET /agents/{id}` - Get graph definition (for eligibility check)
- `POST /agents` - Create agent from file upload
- `POST /agents/{id}/runs` - Start a run (send message)
- `GET /agents/{id}/runs/{run_id}` - Poll for completion

### Session Support

Each conversation uses its ID as the `session_id` when creating runs, enabling multi-turn conversations with LLM memory.

## Configuration

### Environment

The Chat UI proxies API requests to the runtime. Configure in `vite.config.ts`:

```typescript
server: {
  port: 3001,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
    },
  },
}
```

### Runtime Connection

Use the settings modal (gear icon) to configure the runtime URL if not using the default `http://localhost:8000`.

## Tech Stack

- **React 18** with TypeScript
- **Vite** for development and building
- **Zustand** for state management
- **TanStack Query** for API data fetching
- **Tailwind CSS** for styling
- **react-markdown** for message rendering
- **lucide-react** for icons

## Scripts

```bash
npm run dev      # Start development server
npm run build    # Build for production
npm run preview  # Preview production build
npm run lint     # Run ESLint
```

## Related

- [GraphFlow README](../../README.md) - Main project documentation
- [graph-builder](../graph-builder/README.md) - Visual graph construction
- [graph-runtime](../graph-runtime/README.md) - Agent execution service
