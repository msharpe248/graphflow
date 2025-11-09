"""Core Pydantic models for graph definitions."""

import re
from typing import Any, Dict, List, Optional, Set, Tuple
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


class ConfigDefinition(BaseModel):
    """Definition of a configuration value."""
    type: str  # string, number, boolean
    description: Optional[str] = None

    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid_types = {'string', 'number', 'boolean'}
        if v not in valid_types:
            raise ValueError(f'type must be one of {valid_types}')
        return v


class EnvironmentDefinition(BaseModel):
    """Definition of an environment variable reference."""
    type: str  # string, number, boolean
    key: str  # Environment variable name
    description: Optional[str] = None
    required: bool = True

    @field_validator('type')
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid_types = {'string', 'number', 'boolean'}
        if v not in valid_types:
            raise ValueError(f'type must be one of {valid_types}')
        return v


class MemorySchema(BaseModel):
    """Schema for memory store."""
    inputs: Dict[str, FieldDefinition] = Field(default_factory=dict)
    outputs: Dict[str, FieldDefinition] = Field(default_factory=dict)
    intermediate: Dict[str, FieldDefinition] = Field(default_factory=dict)
    secrets: Dict[str, SecretDefinition] = Field(default_factory=dict)
    config: Dict[str, ConfigDefinition] = Field(default_factory=dict)
    environment: Dict[str, EnvironmentDefinition] = Field(default_factory=dict)


def parse_memory_references(config: Dict[str, Any], outputs: Dict[str, str]) -> Tuple[Set[str], Set[str]]:
    """
    Parse config and outputs dicts to extract memory references.

    Supports namespaced syntax:
    - {memory.field} - Regular memory (inputs/intermediate/outputs)
    - {config.field} - Configuration values
    - {env.field} - Environment variables
    - {secrets.field} - Secrets

    Args:
        config: Step configuration dict
        outputs: Step outputs dict (maps output names to memory locations)

    Returns:
        Tuple of (reads, writes) where each is a set of memory keys with namespace prefix
        Example: {"memory.user_input", "config.backend_url", "env.API_KEY"}
    """
    reads = set()
    writes = set()

    # Pattern to match {namespace.variable} where namespace is memory, config, env, or secrets
    pattern = re.compile(r'\{(memory|config|env|secrets)\.([^}]+)\}')

    def scan_value(value: Any, is_output: bool = False):
        """Recursively scan a value for memory references."""
        if isinstance(value, str):
            # Find all {namespace.field} references
            for match in pattern.finditer(value):
                namespace = match.group(1)
                field_key = match.group(2)
                full_key = f"{namespace}.{field_key}"
                if is_output:
                    writes.add(full_key)
                else:
                    reads.add(full_key)
        elif isinstance(value, dict):
            for v in value.values():
                scan_value(v, is_output)
        elif isinstance(value, list):
            for item in value:
                scan_value(item, is_output)

    # Scan config for reads
    scan_value(config, is_output=False)

    # Scan outputs for writes
    scan_value(outputs, is_output=True)

    return reads, writes


class Step(BaseModel):
    """Definition of a graph step/node."""
    id: str
    type: str
    config: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, str] = Field(default_factory=dict)
    description: Optional[str] = None

    @field_validator('id')
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('id cannot be empty')
        return v

    @property
    def memory_reads(self) -> List[str]:
        """Extract memory reads from config by parsing {memory.field} syntax."""
        reads, _ = parse_memory_references(self.config, {})
        return sorted(reads)

    @property
    def memory_writes(self) -> List[str]:
        """Extract memory writes from outputs by parsing {memory.field} syntax."""
        _, writes = parse_memory_references({}, self.outputs)
        return sorted(writes)


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

        # Check that memory references in config and outputs point to valid memory keys
        # Build set of namespaced keys (e.g., "memory.url", "config.api_url")
        all_namespaced_keys = (
            {f"memory.{k}" for k in self.memory.inputs.keys()} |
            {f"memory.{k}" for k in self.memory.outputs.keys()} |
            {f"memory.{k}" for k in self.memory.intermediate.keys()} |
            {f"config.{k}" for k in self.memory.config.keys()} |
            {f"env.{k}" for k in self.memory.environment.keys()} |
            {f"secrets.{k}" for k in self.memory.secrets.keys()}
        )

        for step in self.steps:
            # Parse memory references from config and outputs
            reads, writes = parse_memory_references(step.config, step.outputs)

            # Validate reads - check for namespaced key match
            for key in reads:
                if key not in all_namespaced_keys:
                    errors.append(
                        f"Step {step.id}: memory reference '{{{key}}}' in config "
                        f"references undeclared memory key '{key}'"
                    )

            # Validate writes - check for namespaced key match
            # Only memory namespace can be written to (config/env/secrets validated at runtime)
            for key in writes:
                if key.startswith("memory.") and key not in all_namespaced_keys:
                    errors.append(
                        f"Step {step.id}: memory reference '{{{key}}}' in outputs "
                        f"references undeclared memory key '{key}'"
                    )

        return errors
