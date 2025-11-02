# GraphFlow Examples

This directory contains example graph definitions demonstrating various features of GraphFlow.

## Examples

### simple_agent.json
A basic agent that demonstrates:
- Linear flow (start → transform → transform → output)
- Memory reads and writes
- Transform steps with Python code
- Input/output mapping

**Usage:**
```bash
python validate_example.py simple_agent.json
```

### conditional_agent.json
A more complex agent demonstrating:
- Conditional branching based on input values
- Multiple execution paths
- Join step for synchronization
- Conditional edges
- Dynamic message selection

**Usage:**
```bash
python validate_example.py conditional_agent.json
```

## Validating Examples

To validate all examples:
```bash
python validate_example.py
```

To validate a specific example:
```bash
python validate_example.py simple_agent.json
```

## Graph Definition Structure

Each graph JSON file contains:
- **version**: Schema version (currently "1.0")
- **metadata**: Name, description, tags, etc.
- **memory**: Schema for inputs, outputs, intermediate values, and secrets
- **steps**: Array of step definitions (nodes in the graph)
- **edges**: Array of edge definitions (control flow)

## Creating Your Own

To create your own graph definition:

1. Copy one of the examples
2. Modify the metadata, memory schema, steps, and edges
3. Validate using `validate_example.py`
4. Test execution using the runtime (once available)

## Step Types Available

- **start**: Entry point (no operation)
- **output**: Map intermediate values to outputs
- **conditional**: Evaluate conditions for branching
- **transform**: Execute Python code to transform data
- **join**: Synchronization point for multiple branches

More step types will be added in future phases (llm, http, db_query, etc.).
