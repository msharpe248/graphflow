"""Main entry point for GraphFlow Runtime."""

import os
import subprocess
from pathlib import Path

import click
import uvicorn


def get_default_cert_dir() -> Path:
    """Get default certificate directory path (project root/.certs)."""
    # Navigate from this file to project root
    return Path(__file__).parent.parent.parent.parent / ".certs"


def resolve_cert_paths(
    ssl_keyfile: str | None,
    ssl_certfile: str | None,
    cert_dir: str | None,
) -> tuple[str | None, str | None]:
    """Resolve certificate paths from explicit paths or directory."""
    if ssl_keyfile and ssl_certfile:
        return ssl_keyfile, ssl_certfile

    # Use cert_dir to find certificates
    dir_path = Path(cert_dir) if cert_dir else get_default_cert_dir()
    key_path = dir_path / "graphflow.key"
    cert_path = dir_path / "graphflow.crt"

    if key_path.exists() and cert_path.exists():
        return str(key_path), str(cert_path)

    return None, None


def generate_certificates(cert_dir: Path) -> tuple[str, str]:
    """Generate self-signed certificates using OpenSSL."""
    cert_dir.mkdir(parents=True, exist_ok=True)
    key_path = cert_dir / "graphflow.key"
    cert_path = cert_dir / "graphflow.crt"

    print(f"Generating self-signed certificates in {cert_dir}/...")

    cmd = [
        "openssl", "req", "-x509", "-nodes", "-days", "365",
        "-newkey", "rsa:2048",
        "-keyout", str(key_path),
        "-out", str(cert_path),
        "-subj", "/CN=localhost",
        "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1,IP:::1"
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise click.ClickException(f"Failed to generate certificates: {e.stderr}")
    except FileNotFoundError:
        raise click.ClickException(
            "OpenSSL is required to generate certificates. "
            "Please install OpenSSL or provide certificate files manually."
        )

    key_path.chmod(0o600)
    cert_path.chmod(0o644)

    print(f"  Generated: {key_path}")
    print(f"  Generated: {cert_path}")

    return str(key_path), str(cert_path)


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
@click.option(
    "--ssl-keyfile",
    type=click.Path(exists=True),
    envvar="GRAPHFLOW_SSL_KEYFILE",
    help="Path to SSL private key file"
)
@click.option(
    "--ssl-certfile",
    type=click.Path(exists=True),
    envvar="GRAPHFLOW_SSL_CERTFILE",
    help="Path to SSL certificate file"
)
@click.option(
    "--cert-dir",
    type=click.Path(),
    envvar="GRAPHFLOW_CERT_DIR",
    help="Directory containing certificates (default: .certs)"
)
@click.option(
    "--auto-ssl/--no-auto-ssl",
    default=True,
    envvar="GRAPHFLOW_AUTO_SSL",
    help="Auto-generate self-signed certs if not present (default: enabled)"
)
@click.option(
    "--insecure", "-k",
    is_flag=True,
    envvar="GRAPHFLOW_INSECURE",
    help="Skip SSL certificate verification in client calls"
)
def main(
    host: str,
    port: int,
    reload: bool,
    workers: int,
    ssl_keyfile: str | None,
    ssl_certfile: str | None,
    cert_dir: str | None,
    auto_ssl: bool,
    insecure: bool,
):
    """
    Start GraphFlow Runtime server with HTTPS support.

    Examples:
        # Start with auto-generated certificates (default)
        graphflow-runtime

        # Start with custom certificates
        graphflow-runtime --ssl-keyfile /path/to/key --ssl-certfile /path/to/cert

        # Start with certificates from a custom directory
        graphflow-runtime --cert-dir /path/to/certs

        # Skip certificate generation (HTTP mode - not recommended)
        graphflow-runtime --no-auto-ssl

        # Enable insecure mode for development with self-signed certs
        graphflow-runtime --insecure

        # Development mode with auto-reload
        graphflow-runtime --reload

        # Production with multiple workers
        graphflow-runtime --workers 4

    Environment variables:
        GRAPHFLOW_SSL_KEYFILE   - Path to SSL private key
        GRAPHFLOW_SSL_CERTFILE  - Path to SSL certificate
        GRAPHFLOW_CERT_DIR      - Certificate directory (default: .certs)
        GRAPHFLOW_AUTO_SSL      - Auto-generate certs (default: true)
        GRAPHFLOW_INSECURE      - Skip SSL verification (default: false)
    """
    # Set insecure mode in environment for other components to read
    if insecure:
        os.environ["GRAPHFLOW_INSECURE"] = "true"

    # Resolve certificate paths
    resolved_keyfile, resolved_certfile = resolve_cert_paths(
        ssl_keyfile, ssl_certfile, cert_dir
    )

    # Auto-generate certificates if needed
    if auto_ssl and not (resolved_keyfile and resolved_certfile):
        target_dir = Path(cert_dir) if cert_dir else get_default_cert_dir()
        resolved_keyfile, resolved_certfile = generate_certificates(target_dir)

    # Determine protocol
    is_https = bool(resolved_keyfile and resolved_certfile)
    protocol = "https" if is_https else "http"

    print(f"Starting GraphFlow Runtime on {protocol}://{host}:{port}")
    print(f"Documentation available at: {protocol}://{host}:{port}/docs")

    if is_https:
        print(f"SSL Key: {resolved_keyfile}")
        print(f"SSL Cert: {resolved_certfile}")

    if insecure:
        print("Insecure mode: SSL verification disabled for client calls")

    print()

    # Build uvicorn configuration
    uvicorn_config = {
        "app": "graphflow_runtime.app:app",
        "host": host,
        "port": port,
        "reload": reload,
        "workers": workers if not reload else 1,  # Can't use workers with reload
    }

    if resolved_keyfile and resolved_certfile:
        uvicorn_config["ssl_keyfile"] = resolved_keyfile
        uvicorn_config["ssl_certfile"] = resolved_certfile

    uvicorn.run(**uvicorn_config)


if __name__ == "__main__":
    main()
