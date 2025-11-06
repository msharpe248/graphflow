"""
Test core GraphFlow functionality.

Tests for graph-core package including graph definition, memory store,
step registry, and step execution.
"""

import pytest
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


class TestGraphDefinition:
    """Test graph definition and validation."""

    def test_create_graph_definition(self):
        """Test creating a valid graph definition."""
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
            ],
            edges=[
                Edge(id="e1", **{"from": "start_1", "to": "transform_1"}),
            ]
        )

        assert graph.metadata.name == "Test Agent"
        assert len(graph.steps) == 2
        assert len(graph.edges) == 1

    def test_validate_graph_structure(self):
        """Test graph structure validation."""
        graph = GraphDefinition(
            version="1.0",
            metadata=Metadata(name="Test", description="Test"),
            memory=MemorySchema(
                inputs={"input": FieldDefinition(type="string")},
                outputs={"output": FieldDefinition(type="string")},
                intermediate={}
            ),
            steps=[Step(id="step1", type="start", config={})],
            edges=[]
        )

        errors = graph.validate_graph_structure()
        assert errors == []  # Should be valid

    def test_graph_json_export_import(self):
        """Test exporting and re-importing graph as JSON."""
        graph = GraphDefinition(
            version="1.0",
            metadata=Metadata(name="Test", description="Test"),
            memory=MemorySchema(
                inputs={"input": FieldDefinition(type="string")},
                outputs={"output": FieldDefinition(type="string")},
                intermediate={}
            ),
            steps=[Step(id="step1", type="start", config={})],
            edges=[]
        )

        # Export to JSON
        graph_json = graph.model_dump_json(indent=2, by_alias=True)
        assert len(graph_json) > 0

        # Re-import
        reimported_graph = GraphDefinition.model_validate_json(graph_json)
        assert reimported_graph.metadata.name == "Test"
        assert len(reimported_graph.steps) == 1


class TestMemoryStore:
    """Test memory store functionality."""

    @pytest.fixture
    def memory_schema(self):
        """Create a test memory schema."""
        return MemorySchema(
            inputs={
                "input_value": FieldDefinition(type="string", required=True)
            },
            outputs={
                "output_value": FieldDefinition(type="string", required=True)
            },
            intermediate={
                "temp_value": FieldDefinition(type="string", required=False)
            }
        )

    def test_memory_initialization(self, memory_schema):
        """Test initializing memory with inputs."""
        memory = MemoryStore(schema=memory_schema)
        memory.initialize_inputs({"input_value": "hello world"})

        assert memory.read("input_value") == "hello world"

    def test_memory_read_write(self, memory_schema):
        """Test reading and writing to memory."""
        memory = MemoryStore(schema=memory_schema)
        memory.initialize_inputs({"input_value": "test"})

        # Write to intermediate
        memory.write("temp_value", "transformed")
        assert memory.read("temp_value") == "transformed"

        # Write to output
        memory.write("output_value", "final")
        assert memory.read("output_value") == "final"

    def test_get_all_outputs(self, memory_schema):
        """Test retrieving all outputs."""
        memory = MemoryStore(schema=memory_schema)
        memory.initialize_inputs({"input_value": "test"})
        memory.write("output_value", "result")

        outputs = memory.get_all_outputs()
        assert outputs == {"output_value": "result"}


class TestStepRegistry:
    """Test step registry functionality."""

    def test_list_registered_types(self):
        """Test listing registered step types."""
        types = StepRegistry.list_types()

        assert isinstance(types, list)
        assert len(types) > 0
        assert "start" in types
        assert "output" in types
        assert "transform" in types

    def test_get_step_class(self):
        """Test retrieving step class from registry."""
        step_class = StepRegistry.get("start")
        assert step_class is not None
        assert hasattr(step_class, "execute")

    def test_get_nonexistent_step(self):
        """Test retrieving non-existent step type."""
        with pytest.raises((KeyError, ValueError)):
            StepRegistry.get("nonexistent_step_type")


class TestStepExecution:
    """Test step execution."""

    @pytest.fixture
    def memory_store(self):
        """Create a memory store for testing."""
        schema = MemorySchema(
            inputs={"input_value": FieldDefinition(type="string")},
            outputs={"output_value": FieldDefinition(type="string")},
            intermediate={"transformed_value": FieldDefinition(type="string")}
        )
        memory = MemoryStore(schema=schema)
        memory.initialize_inputs({"input_value": "hello world"})
        return memory

    @pytest.mark.asyncio
    async def test_start_step_execution(self, memory_store):
        """Test executing start step."""
        start_step_class = StepRegistry.get("start")
        start_step = start_step_class(
            id="start_1",
            config={},
            outputs={}
        )

        # Should execute without error (no-op)
        await start_step.execute(memory_store)

    @pytest.mark.asyncio
    async def test_transform_step_execution(self, memory_store):
        """Test executing transform step."""
        transform_step_class = StepRegistry.get("transform")
        transform_step = transform_step_class(
            id="transform_1",
            config={
                "operation": "uppercase",
                "code": "return {memory.input_value}.upper()"
            },
            outputs={"result": "{memory.transformed_value}"}
        )

        await transform_step.execute(memory_store)

        result = memory_store.read("transformed_value")
        assert result == "HELLO WORLD"

    @pytest.mark.asyncio
    async def test_output_step_execution(self, memory_store):
        """Test executing output step."""
        # First add intermediate value
        memory_store.write("transformed_value", "test result")

        output_step_class = StepRegistry.get("output")
        output_step = output_step_class(
            id="output_1",
            config={},
            outputs={"output_value": "{memory.transformed_value}"}
        )

        await output_step.execute(memory_store)

        outputs = memory_store.get_all_outputs()
        assert outputs["output_value"] == "test result"


class TestEndToEndWorkflow:
    """Test complete workflow from graph to execution."""

    @pytest.mark.asyncio
    async def test_complete_graph_execution(self):
        """Test executing a complete graph workflow."""
        # Create graph
        graph = GraphDefinition(
            version="1.0",
            metadata=Metadata(name="Test", description="Test"),
            memory=MemorySchema(
                inputs={"input": FieldDefinition(type="string")},
                outputs={"output": FieldDefinition(type="string")},
                intermediate={"temp": FieldDefinition(type="string")}
            ),
            steps=[
                Step(id="start_1", type="start", config={}),
                Step(
                    id="transform_1",
                    type="transform",
                    config={
                        "operation": "uppercase",
                        "code": "return {memory.input}.upper()"
                    },
                    outputs={"result": "{memory.temp}"}
                ),
                Step(
                    id="output_1",
                    type="output",
                    config={},
                    outputs={"output": "{memory.temp}"}
                )
            ],
            edges=[
                Edge(id="e1", **{"from": "start_1", "to": "transform_1"}),
                Edge(id="e2", **{"from": "transform_1", "to": "output_1"}),
            ]
        )

        # Validate
        errors = graph.validate_graph_structure()
        assert errors == []

        # Create memory
        memory = MemoryStore(schema=graph.memory)
        memory.initialize_inputs({"input": "hello"})

        # Execute steps in order
        for step_def in graph.steps:
            step_class = StepRegistry.get(step_def.type)
            step = step_class(
                id=step_def.id,
                config=step_def.config,
                outputs=step_def.outputs
            )
            await step.execute(memory)

        # Check final output
        outputs = memory.get_all_outputs()
        assert outputs["output"] == "HELLO"
