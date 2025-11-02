"""FastAPI application for GraphFlow Runtime."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from graphflow_runtime.storage.database import init_db
from graphflow_runtime.executor.async_executor import AsyncExecutor
from graphflow_runtime.api import routes


# Global executor instance
executor = AsyncExecutor()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    # Startup
    init_db()
    routes.executor = executor
    print("✓ Database initialized")
    print("✓ Executor started")

    yield

    # Shutdown
    await executor.shutdown()
    print("✓ Executor shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="GraphFlow Runtime",
    description="Runtime manager for GraphFlow agents",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(routes.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "GraphFlow Runtime",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }
