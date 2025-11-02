"""Script to validate example graph definitions."""

import json
import sys
from pathlib import Path
from graphflow_core import GraphDefinition


def validate_graph_file(file_path: Path) -> bool:
    """
    Validate a graph definition file.

    Args:
        file_path: Path to JSON file

    Returns:
        True if valid, False otherwise
    """
    print(f"\nValidating: {file_path.name}")
    print("=" * 60)

    try:
        # Load JSON
        with open(file_path) as f:
            data = json.load(f)

        # Parse as GraphDefinition
        graph = GraphDefinition(**data)

        # Basic info
        print(f"Name: {graph.metadata.name}")
        print(f"Description: {graph.metadata.description}")
        print(f"Version: {graph.version}")
        print(f"\nComponents:")
        print(f"  - Steps: {len(graph.steps)}")
        print(f"  - Edges: {len(graph.edges)}")
        print(f"  - Inputs: {len(graph.memory.inputs)}")
        print(f"  - Outputs: {len(graph.memory.outputs)}")
        print(f"  - Intermediate: {len(graph.memory.intermediate)}")

        # Validate structure
        errors = graph.validate_graph_structure()
        if errors:
            print(f"\n✗ Validation errors:")
            for error in errors:
                print(f"  - {error}")
            return False

        # List steps
        print(f"\nSteps:")
        for step in graph.steps:
            desc = f" - {step.description}" if step.description else ""
            print(f"  - {step.id} ({step.type}){desc}")

        # List edges
        print(f"\nEdges:")
        for edge in graph.edges:
            cond = f" [if {edge.condition}]" if edge.condition else ""
            print(f"  - {edge.source} → {edge.target}{cond}")

        print(f"\n✓ Valid graph definition")
        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Validate all example graphs or a specific file."""
    if len(sys.argv) > 1:
        # Validate specific file
        file_path = Path(sys.argv[1])
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            sys.exit(1)
        success = validate_graph_file(file_path)
        sys.exit(0 if success else 1)
    else:
        # Validate all examples
        examples_dir = Path(__file__).parent
        json_files = list(examples_dir.glob("*.json"))

        if not json_files:
            print("No example JSON files found")
            sys.exit(1)

        print(f"Found {len(json_files)} example files")

        results = []
        for json_file in sorted(json_files):
            success = validate_graph_file(json_file)
            results.append((json_file.name, success))

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        for name, success in results:
            status = "✓" if success else "✗"
            print(f"{status} {name}")

        all_valid = all(success for _, success in results)
        print(f"\nResult: {'All valid' if all_valid else 'Some errors'}")
        sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
