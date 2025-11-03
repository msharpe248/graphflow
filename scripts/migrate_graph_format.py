#!/usr/bin/env python3
"""
Migration script to convert GraphFlow graph JSON files from old format to new format.

Changes:
1. Template syntax: {{variable}} → {memory.variable}
2. Remove memory_reads and memory_writes fields from steps
3. Convert *_key config fields to outputs object with {memory.field} syntax
4. Add description field to steps (optional, defaults to None)

Usage:
    python scripts/migrate_graph_format.py <input.json> [output.json]

    If output.json is not specified, will overwrite input.json
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List


def migrate_template_syntax(value: Any) -> Any:
    """
    Recursively convert {{variable}} to {memory.variable} in strings.

    Handles nested dicts and lists.
    """
    if isinstance(value, str):
        # Replace {{variable}} with {memory.variable}
        # Pattern: {{ followed by word characters and dots, followed by }}
        pattern = r'\{\{([a-zA-Z0-9_.]+)\}\}'
        return re.sub(pattern, r'{memory.\1}', value)
    elif isinstance(value, dict):
        return {k: migrate_template_syntax(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [migrate_template_syntax(item) for item in value]
    else:
        return value


def extract_outputs_from_config(config: Dict[str, Any], step_type: str) -> Dict[str, str]:
    """
    Extract *_key fields from config and convert to outputs dict.

    Common patterns:
    - response_key: "api_data" → outputs: {"response": "{memory.api_data}"}
    - output_key: "result" → outputs: {"output": "{memory.result}"}
    - status_code_key, headers_key, etc.

    Special case for output steps:
    - config.mapping: {"out1": "src1", "out2": "src2"} → outputs: {"out1": "{memory.src1}", "out2": "{memory.src2}"}

    Returns outputs dict and list of keys to remove from config.
    """
    outputs = {}
    keys_to_remove = []

    # Special case for output steps - convert mapping to outputs
    if step_type == 'output' and 'mapping' in config:
        mapping = config['mapping']
        if isinstance(mapping, dict):
            for output_name, source_field in mapping.items():
                # Convert to {memory.field} format
                if isinstance(source_field, str):
                    if source_field.startswith('{memory.') and source_field.endswith('}'):
                        outputs[output_name] = source_field
                    else:
                        outputs[output_name] = f"{{memory.{source_field}}}"
            # Don't remove mapping from config - it stays for backward compat
        return outputs, keys_to_remove

    # Standard _key pattern
    for key, value in config.items():
        if key.endswith('_key'):
            # Extract output name (everything before _key)
            output_name = key[:-4]  # Remove '_key' suffix

            # Convert value to {memory.field} format
            if isinstance(value, str):
                # If it already has {memory.field} format, keep it
                if value.startswith('{memory.') and value.endswith('}'):
                    outputs[output_name] = value
                else:
                    # Otherwise wrap it
                    outputs[output_name] = f"{{memory.{value}}}"

                keys_to_remove.append(key)

    return outputs, keys_to_remove


def migrate_step(step: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate a single step to new format.

    Changes:
    1. Migrate template syntax in config
    2. Extract outputs from *_key fields in config
    3. Remove memory_reads and memory_writes
    4. Add description field if not present
    """
    migrated = {}

    # Copy basic fields
    migrated['id'] = step['id']
    migrated['type'] = step['type']

    # Migrate config
    config = migrate_template_syntax(step.get('config', {}))

    # Extract outputs from *_key fields
    outputs, keys_to_remove = extract_outputs_from_config(config, step['type'])

    # Remove *_key fields from config
    for key in keys_to_remove:
        del config[key]

    migrated['config'] = config

    # Add outputs (may be empty dict)
    migrated['outputs'] = outputs

    # Add description if it exists in old format
    if 'description' in step:
        migrated['description'] = step['description']

    # Note: memory_reads and memory_writes are intentionally omitted
    # They will be computed dynamically from config and outputs

    return migrated


def migrate_graph(graph: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate entire graph definition to new format.
    """
    migrated = {
        'version': graph.get('version', '1.0'),
        'metadata': graph['metadata'],
        'memory': graph['memory'],
        'steps': [migrate_step(step) for step in graph['steps']],
        'edges': graph['edges'],
    }

    return migrated


def migrate_file(input_path: Path, output_path: Path, verbose: bool = True):
    """
    Migrate a graph JSON file from old format to new format.
    """
    if verbose:
        print(f"Reading {input_path}...")

    with open(input_path, 'r') as f:
        graph = json.load(f)

    if verbose:
        print(f"Migrating {len(graph.get('steps', []))} steps...")

    migrated = migrate_graph(graph)

    if verbose:
        print(f"Writing {output_path}...")

    with open(output_path, 'w') as f:
        json.dump(migrated, f, indent=2)

    if verbose:
        print(f"✓ Migration complete!")


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    input_path = Path(sys.argv[1])

    if not input_path.exists():
        print(f"Error: File not found: {input_path}")
        sys.exit(1)

    # Determine output path
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        # Overwrite input file
        output_path = input_path
        print(f"Warning: Will overwrite {input_path}")
        response = input("Continue? [y/N] ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)

    try:
        migrate_file(input_path, output_path)
    except Exception as e:
        print(f"Error during migration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
