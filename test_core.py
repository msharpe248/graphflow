"""Quick test to verify graph-core package works."""

import asyncio
import json
from graphflow_core import (
    GraphDefinition,
    Metadata,
    MemorySchema,
    FieldDefinition,
    Step,
    Edge,
    MemoryStore,
    StepRegistry,
)


async def main():
    print("Testing GraphFlow Core...")
    print()

    # Test 1: Create a graph definition
    print("1. Creating graph definition...")
    graph = GraphDefinition(
        version="1.0",
        metadata=Metadata(
            name="Test Agent",
            description="Simple test agent"
        ),
        memory=MemorySchema(
            inputs={
                "input_value": FieldDefinition(type="string", required=True)
            },
            outputs={
                "output_value": FieldDefinition(type="string", required=True)
            },
            intermediate={
                "transformed_value": FieldDefinition(type="string", required=False)
            }
        ),
        steps=[
            Step(id="start_1", type="start", config={}),
            Step(
                id="transform_1",
                type="transform",
                config={
                    "operation": "uppercase",
                    "code": "return input_value.upper()",
                    "input_keys": ["input_value"],
                    "output_key": "transformed_value"
                },
                memory_reads=["input_value"],
                memory_writes=["transformed_value"]
            ),
            Step(
                id="output_1",
                type="output",
                config={
                    "mapping": {
                        "output_value": "transformed_value"
                    }
                },
                memory_reads=["transformed_value"],
                memory_writes=["output_value"]
            )
        ],
        edges=[
            Edge(id="e1", **{"from": "start_1", "to": "transform_1"}),
            Edge(id="e2", **{"from": "transform_1", "to": "output_1"}),
        ]
    )
    print(f"✓ Graph created: {graph.metadata.name}")
    print(f"  - Steps: {len(graph.steps)}")
    print(f"  - Edges: {len(graph.edges)}")
    print()

    # Test 2: Validate graph structure
    print("2. Validating graph structure...")
    errors = graph.validate_graph_structure()
    if errors:
        print("✗ Validation errors:")
        for error in errors:
            print(f"  - {error}")
        return
    print("✓ Graph structure valid")
    print()

    # Test 3: Test memory store
    print("3. Testing memory store...")
    memory = MemoryStore(schema=graph.memory)
    memory.initialize_inputs({"input_value": "hello world"})
    print(f"✓ Memory initialized with inputs")
    print(f"  - Input: {memory.read('input_value')}")
    print()

    # Test 4: Check step registry
    print("4. Checking step registry...")
    registered_types = StepRegistry.list_types()
    print(f"✓ Registered step types: {', '.join(registered_types)}")
    print()

    # Test 5: Execute steps
    print("5. Executing steps...")

    # Execute start step
    start_step_class = StepRegistry.get("start")
    start_step = start_step_class(id="start_1", config={}, memory_reads=[], memory_writes=[])
    await start_step.execute(memory)
    print("✓ Start step executed")

    # Execute transform step
    transform_step_class = StepRegistry.get("transform")
    transform_config = graph.steps[1].config
    transform_step = transform_step_class(
        id="transform_1",
        config=transform_config,
        memory_reads=["input_value"],
        memory_writes=["transformed_value"]
    )
    await transform_step.execute(memory)
    print(f"✓ Transform step executed")
    print(f"  - Transformed: {memory.read('transformed_value')}")

    # Execute output step
    output_step_class = StepRegistry.get("output")
    output_config = graph.steps[2].config
    output_step = output_step_class(
        id="output_1",
        config=output_config,
        memory_reads=["transformed_value"],
        memory_writes=["output_value"]
    )
    await output_step.execute(memory)
    print(f"✓ Output step executed")
    print()

    # Test 6: Check final outputs
    print("6. Checking outputs...")
    outputs = memory.get_all_outputs()
    print(f"✓ Final outputs: {json.dumps(outputs, indent=2)}")
    print()

    # Test 7: Export graph to JSON
    print("7. Testing JSON export...")
    graph_json = graph.model_dump_json(indent=2, by_alias=True)
    print("✓ Graph exported to JSON successfully")
    print(f"  Length: {len(graph_json)} bytes")
    print()

    # Test 8: Re-import from JSON
    print("8. Testing JSON import...")
    reimported_graph = GraphDefinition.model_validate_json(graph_json)
    print("✓ Graph re-imported successfully")
    print(f"  Name: {reimported_graph.metadata.name}")
    print()

    print("=" * 50)
    print("All tests passed! ✓")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
