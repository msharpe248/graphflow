"""Command-line interface for GraphFlow compiler."""

import json
import sys
from pathlib import Path
import click
from graphflow_core.models import GraphDefinition
from graphflow_core.plugins.loader import PluginLoader
from graphflow_compiler import compile_graph, CompilerRegistry


def _load_plugins():
    """Load all available GraphFlow plugins to register their steps."""
    loader = PluginLoader()
    plugins = loader.discover_plugins()

    # Also try to import graphflow_ai directly if available
    try:
        import graphflow_ai
    except ImportError:
        pass

    return plugins


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    GraphFlow Compiler - Transpile graph definitions to executable Python code.

    Examples:

        # Compile to Pydantic AI
        graphflow-compile compile graph.json --framework pydantic_ai --output agent.py

        # Compile to LangGraph
        graphflow-compile compile graph.json --framework langgraph --output agent.py

        # Compile for runtime (no standalone wrappers)
        graphflow-compile compile graph.json --no-standalone --output agent.py

        # Validate graph without compiling
        graphflow-compile validate graph.json
    """
    # Load plugins on CLI startup
    _load_plugins()


@cli.command()
@click.argument('graph_file', type=click.Path(exists=True, path_type=Path))
@click.option(
    '--framework', '-f',
    type=click.Choice(['pydantic_ai', 'langgraph']),
    default='pydantic_ai',
    help='Target framework for code generation'
)
@click.option(
    '--output', '-o',
    type=click.Path(path_type=Path),
    help='Output file path (default: stdout)'
)
@click.option(
    '--standalone/--no-standalone',
    default=True,
    help='Include standalone execution wrappers (CLI/FastAPI)'
)
@click.option(
    '--validate-only',
    is_flag=True,
    help='Only validate graph without generating code'
)
def compile(graph_file: Path, framework: str, output: Path, standalone: bool, validate_only: bool):
    """
    Compile a graph definition file to Python code.

    GRAPH_FILE: Path to graph definition JSON file
    """
    try:
        # Load graph definition
        click.echo(f"Loading graph from {graph_file}...")
        with open(graph_file) as f:
            graph_data = json.load(f)

        graph = GraphDefinition(**graph_data)
        click.echo(f"✓ Loaded: {graph.metadata.name}")

        # Validate graph structure
        click.echo("Validating graph structure...")
        errors = graph.validate_graph_structure()
        if errors:
            click.echo("✗ Validation errors:", err=True)
            for error in errors:
                click.echo(f"  - {error}", err=True)
            sys.exit(1)

        click.echo("✓ Graph structure valid")

        if validate_only:
            click.echo("\nValidation complete!")
            return

        # Compile graph
        click.echo(f"\nCompiling to {framework}...")
        code = compile_graph(graph, framework=framework, standalone=standalone)
        click.echo("✓ Compilation successful")

        # Output
        if output:
            output.write_text(code)
            click.echo(f"\n✓ Code written to {output}")
            click.echo(f"\nTo run the generated agent:")
            click.echo(f"  python {output} inputs.json")
            click.echo(f"  python {output} --server  # Run as FastAPI server")
        else:
            click.echo("\n" + "=" * 60)
            click.echo(code)
            click.echo("=" * 60)

    except FileNotFoundError as e:
        click.echo(f"✗ Error: File not found: {e}", err=True)
        sys.exit(1)
    except json.JSONDecodeError as e:
        click.echo(f"✗ Error: Invalid JSON: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        if '--debug' in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument('graph_file', type=click.Path(exists=True, path_type=Path))
def validate(graph_file: Path):
    """
    Validate a graph definition file without compiling.

    GRAPH_FILE: Path to graph definition JSON file
    """
    try:
        click.echo(f"Validating {graph_file}...")

        # Load graph
        with open(graph_file) as f:
            graph_data = json.load(f)

        graph = GraphDefinition(**graph_data)

        # Display info
        click.echo(f"\nGraph: {graph.metadata.name}")
        click.echo(f"Description: {graph.metadata.description or 'N/A'}")
        click.echo(f"Version: {graph.version}")
        click.echo(f"\nComponents:")
        click.echo(f"  Steps: {len(graph.steps)}")
        click.echo(f"  Edges: {len(graph.edges)}")
        click.echo(f"  Inputs: {len(graph.memory.inputs)}")
        click.echo(f"  Outputs: {len(graph.memory.outputs)}")

        # Validate structure
        errors = graph.validate_graph_structure()
        if errors:
            click.echo("\n✗ Validation errors:")
            for error in errors:
                click.echo(f"  - {error}")
            sys.exit(1)

        click.echo("\n✓ Graph is valid!")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
def list_frameworks():
    """List available code generation frameworks."""
    frameworks = CompilerRegistry.list_frameworks()
    click.echo("Available frameworks:")
    for fw in frameworks:
        click.echo(f"  - {fw}")


@cli.command()
@click.argument('graph_file', type=click.Path(exists=True, path_type=Path))
def info(graph_file: Path):
    """
    Display detailed information about a graph definition.

    GRAPH_FILE: Path to graph definition JSON file
    """
    try:
        with open(graph_file) as f:
            graph_data = json.load(f)

        graph = GraphDefinition(**graph_data)

        click.echo(f"Graph: {graph.metadata.name}")
        click.echo(f"=" * 60)
        click.echo(f"\nMetadata:")
        click.echo(f"  Name: {graph.metadata.name}")
        click.echo(f"  Description: {graph.metadata.description or 'N/A'}")
        click.echo(f"  Created: {graph.metadata.created}")
        click.echo(f"  Tags: {', '.join(graph.metadata.tags) or 'None'}")
        click.echo(f"  Framework hints: {', '.join(graph.metadata.framework_hints) or 'None'}")

        click.echo(f"\nMemory Schema:")
        click.echo(f"  Inputs ({len(graph.memory.inputs)}):")
        for key, field in graph.memory.inputs.items():
            req = "required" if field.required else "optional"
            click.echo(f"    - {key} ({field.type}, {req}): {field.description or 'N/A'}")

        click.echo(f"  Outputs ({len(graph.memory.outputs)}):")
        for key, field in graph.memory.outputs.items():
            click.echo(f"    - {key} ({field.type}): {field.description or 'N/A'}")

        click.echo(f"  Intermediate ({len(graph.memory.intermediate)}):")
        for key, field in graph.memory.intermediate.items():
            click.echo(f"    - {key} ({field.type}): {field.description or 'N/A'}")

        click.echo(f"\nSteps ({len(graph.steps)}):")
        for step in graph.steps:
            desc = f" - {step.description}" if step.description else ""
            click.echo(f"  {step.id} ({step.type}){desc}")
            if step.memory_reads:
                click.echo(f"    Reads: {', '.join(step.memory_reads)}")
            if step.memory_writes:
                click.echo(f"    Writes: {', '.join(step.memory_writes)}")

        click.echo(f"\nEdges ({len(graph.edges)}):")
        for edge in graph.edges:
            cond = f" [if {edge.condition}]" if edge.condition else ""
            click.echo(f"  {edge.source} → {edge.target}{cond}")

    except Exception as e:
        click.echo(f"✗ Error: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()
