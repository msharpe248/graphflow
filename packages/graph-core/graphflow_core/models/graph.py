"""Core Pydantic models for graph definitions."""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class Metadata(BaseModel):
    """Graph metadata."""
    name: str
    description: Optional[str] = None
    created: datetime = Field(default_factory=datetime.utcnow)
    framework_hints: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class FieldDefinition(BaseModel):
    """Definition of a memory field."""
    type: str  # string, number, boolean, object, array
    description: Optional[str] = None
    required: bool = True
    default: Optional[Any] = None

    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid_types = {'string', 'number', 'boolean', 'object', 'array', 'any'}
        if v not in valid_types:
            raise ValueError(f'type must be one of {valid_types}')
        return v


class SecretDefinition(BaseModel):
    """Definition of a secret."""
    provider: str  # env, vault, aws_secrets
    key: str
    description: Optional[str] = None

    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        valid_providers = {'env', 'vault', 'aws_secrets'}
        if v not in valid_providers:
            raise ValueError(f'provider must be one of {valid_providers}')
        return v


class MemorySchema(BaseModel):
    """Schema for memory store."""
    inputs: Dict[str, FieldDefinition] = Field(default_factory=dict)
    outputs: Dict[str, FieldDefinition] = Field(default_factory=dict)
    intermediate: Dict[str, FieldDefinition] = Field(default_factory=dict)
    secrets: Dict[str, SecretDefinition] = Field(default_factory=dict)


class Step(BaseModel):
    """Definition of a graph step/node."""
    id: str
    type: str
    config: Dict[str, Any] = Field(default_factory=dict)
    memory_reads: List[str] = Field(default_factory=list)
    memory_writes: List[str] = Field(default_factory=list)
    description: Optional[str] = None

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('id cannot be empty')
        return v


class Edge(BaseModel):
    """Definition of a graph edge."""
    id: str
    source: str = Field(alias='from')  # Use 'from' in JSON, 'source' in Python
    target: str = Field(alias='to')    # Use 'to' in JSON, 'target' in Python
    condition: Optional[str] = None
    description: Optional[str] = None

    model_config = {
        'populate_by_name': True  # Allow both 'from'/'to' and 'source'/'target'
    }

    @field_validator('source', 'target')
    @classmethod
    def validate_step_ref(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('step reference cannot be empty')
        return v


class GraphDefinition(BaseModel):
    """Complete graph definition."""
    version: str = "1.0"
    metadata: Metadata
    memory: MemorySchema
    steps: List[Step]
    edges: List[Edge]

    @field_validator('version')
    @classmethod
    def validate_version(cls, v: str) -> str:
        if v != "1.0":
            raise ValueError('Only version 1.0 is currently supported')
        return v

    def get_step(self, step_id: str) -> Optional[Step]:
        """Get step by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None

    def get_edges_from(self, step_id: str) -> List[Edge]:
        """Get all edges originating from a step."""
        return [edge for edge in self.edges if edge.source == step_id]

    def get_edges_to(self, step_id: str) -> List[Edge]:
        """Get all edges targeting a step."""
        return [edge for edge in self.edges if edge.target == step_id]

    def validate_graph_structure(self) -> List[str]:
        """
        Validate graph structure and return list of errors.
        Returns empty list if valid.
        """
        errors = []

        # Check that all edge references point to valid steps
        step_ids = {step.id for step in self.steps}
        for edge in self.edges:
            if edge.source not in step_ids:
                errors.append(f"Edge {edge.id}: source step '{edge.source}' not found")
            if edge.target not in step_ids:
                errors.append(f"Edge {edge.id}: target step '{edge.target}' not found")

        # Check for duplicate step IDs
        seen_ids = set()
        for step in self.steps:
            if step.id in seen_ids:
                errors.append(f"Duplicate step ID: {step.id}")
            seen_ids.add(step.id)

        # Check for duplicate edge IDs
        seen_edge_ids = set()
        for edge in self.edges:
            if edge.id in seen_edge_ids:
                errors.append(f"Duplicate edge ID: {edge.id}")
            seen_edge_ids.add(edge.id)

        # Check that memory_reads and memory_writes reference valid memory keys
        all_memory_keys = (
            set(self.memory.inputs.keys()) |
            set(self.memory.outputs.keys()) |
            set(self.memory.intermediate.keys())
        )

        for step in self.steps:
            for key in step.memory_reads:
                # Allow dotted paths for nested access (e.g., "object.field")
                base_key = key.split('.')[0]
                if base_key not in all_memory_keys:
                    errors.append(
                        f"Step {step.id}: memory_read key '{key}' not in memory schema"
                    )
            for key in step.memory_writes:
                base_key = key.split('.')[0]
                if base_key not in all_memory_keys:
                    errors.append(
                        f"Step {step.id}: memory_write key '{key}' not in memory schema"
                    )

        return errors
