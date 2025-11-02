"""Main entry point for GraphFlow Runtime."""

import click
import uvicorn


@click.command()
@click.option(
    "--host",
    default="0.0.0.0",
    help="Host to bind to"
)
@click.option(
    "--port",
    default=8000,
    help="Port to bind to"
)
@click.option(
    "--reload",
    is_flag=True,
    help="Enable auto-reload (development only)"
)
@click.option(
    "--workers",
    default=1,
    help="Number of worker processes"
)
def main(host: str, port: int, reload: bool, workers: int):
    """
    Start GraphFlow Runtime server.

    Examples:
        # Start server on default port (8000)
        graphflow-runtime

        # Start on custom port
        graphflow-runtime --port 9000

        # Development mode with auto-reload
        graphflow-runtime --reload

        # Production with multiple workers
        graphflow-runtime --workers 4
    """
    print(f"Starting GraphFlow Runtime on {host}:{port}")
    print(f"Documentation available at: http://{host}:{port}/docs")
    print()

    uvicorn.run(
        "graphflow_runtime.app:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1  # Can't use workers with reload
    )


if __name__ == "__main__":
    main()
