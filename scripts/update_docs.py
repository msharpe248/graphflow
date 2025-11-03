#!/usr/bin/env python3
"""
Helper script to update documentation files with new memory reference syntax.

Changes:
1. {{variable}} → {memory.variable} in all examples
2. Remove memory_reads/memory_writes from JSON examples
3. Update prose describing these fields
"""

import re
import sys
from pathlib import Path


def update_template_syntax_in_text(text: str) -> str:
    """Update {{variable}} to {memory.variable} in text."""
    # Pattern to match {{word}} but not already in {memory.word} format
    pattern = r'\{\{([a-zA-Z0-9_.]+)\}\}'
    return re.sub(pattern, r'{memory.\1}', text)


def remove_memory_arrays_from_json(text: str) -> str:
    """Remove memory_reads and memory_writes lines from JSON code blocks."""
    lines = text.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this line has memory_reads or memory_writes
        if re.search(r'"memory_(reads|writes)":\s*\[', line):
            # Skip this line
            # Also check if it's a multi-line array
            if '[' in line and ']' not in line:
                # Multi-line array, skip until we find the closing bracket
                i += 1
                while i < len(lines) and ']' not in lines[i]:
                    i += 1
                i += 1  # Skip the line with ]
                # Also skip trailing comma if next line exists
                if i < len(lines) and lines[i].strip() == ',':
                    i += 1
                continue
            else:
                # Single line array
                i += 1
                # Skip trailing comma if next line exists and is comma-only
                if i < len(lines) and lines[i].strip() == ',':
                    i += 1
                continue

        result.append(line)
        i += 1

    return '\n'.join(result)


def update_description_text(text: str) -> str:
    """Update prose descriptions about memory fields."""

    # Update references to memory_reads/memory_writes in prose
    replacements = [
        (r'`memory_reads`\s+and\s+`memory_writes`\s+arrays', '`outputs` object'),
        (r'`memory_reads`/`memory_writes`', 'memory references in config and outputs'),
        (r'memory_reads and memory_writes', 'memory references'),
        (r'All keys in `memory_reads`/`memory_writes`', 'All memory keys referenced'),
    ]

    for pattern, replacement in replacements:
        text = re.sub(pattern, replacement, text)

    return text


def update_file(input_path: Path, output_path: Path):
    """Update a documentation file."""
    with open(input_path, 'r') as f:
        content = f.read()

    # Apply transformations
    content = update_template_syntax_in_text(content)
    content = remove_memory_arrays_from_json(content)
    content = update_description_text(content)

    with open(output_path, 'w') as f:
        f.write(content)

    print(f"Updated {input_path} -> {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python update_docs.py <file.md> [output.md]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else input_path

    if output_path == input_path:
        print(f"Warning: Will overwrite {input_path}")
        response = input("Continue? [y/N] ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)

    update_file(input_path, output_path)


if __name__ == '__main__':
    main()
