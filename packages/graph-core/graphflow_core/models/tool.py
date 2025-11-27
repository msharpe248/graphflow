"""Tool definition models for LLM tool support."""

from typing import Literal, Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ToolPropertyMapping(BaseModel):
    """
    Defines how a step property is mapped when used as a tool.

    Each property can be either:
    - LLM-controlled: The LLM provides this value as a tool parameter
    - Runtime-provided: The value comes from memory or a constant
    """

    source_property: str = Field(
        ...,
        description="Property key from the source step's config schema"
    )

    visibility: Literal["llm", "runtime"] = Field(
        ...,
        description="Who controls this property: 'llm' for tool parameter, 'runtime' for hidden"
    )

    # For runtime properties
    runtime_value: Optional[str] = Field(
        None,
        description="If visibility='runtime': constant value or memory binding like {memory.api_key}"
    )

    # For LLM properties
    llm_parameter_name: Optional[str] = Field(
        None,
        description="If visibility='llm': parameter name exposed to LLM (defaults to source_property)"
    )

    llm_description: Optional[str] = Field(
        None,
        description="If visibility='llm': description shown to LLM for this parameter"
    )

    llm_schema: Optional[Dict[str, Any]] = Field(
        None,
        description="If visibility='llm': JSON schema for this parameter (type, enum, etc.)"
    )

    required: bool = Field(
        True,
        description="If visibility='llm': whether this parameter is required"
    )


class ToolDefinition(BaseModel):
    """
    Defines a tool that wraps an existing step for LLM use.

    Tools are created by:
    1. Selecting a source step type (e.g., http_get, db_query)
    2. Configuring which properties the LLM controls vs runtime provides
    3. Defining tool metadata (name, description) for the LLM

    The tool definition is stored in the graph JSON within the LLM step's config.
    At compile time, it's converted to framework-specific tool code.
    """

    id: str = Field(
        ...,
        description="Unique identifier for this tool within the step"
    )

    name: str = Field(
        ...,
        description="Tool name visible to LLM (e.g., 'search_web', 'get_user')"
    )

    description: str = Field(
        ...,
        description="Tool description for LLM explaining when/how to use it"
    )

    source_step_type: str = Field(
        ...,
        description="Step type to wrap (e.g., 'http.HTTPGetStep', 'db_query')"
    )

    property_mappings: List[ToolPropertyMapping] = Field(
        default_factory=list,
        description="How each step property is handled"
    )

    # Output configuration
    output_key: str = Field(
        "result",
        description="Which output from the step to return to LLM"
    )

    output_transform: Optional[str] = Field(
        None,
        description="Optional Python expression to transform output (e.g., 'result[\"data\"]')"
    )

    def get_llm_parameters(self) -> List[ToolPropertyMapping]:
        """Get all LLM-controlled parameters."""
        return [m for m in self.property_mappings if m.visibility == "llm"]

    def get_runtime_parameters(self) -> List[ToolPropertyMapping]:
        """Get all runtime-provided parameters."""
        return [m for m in self.property_mappings if m.visibility == "runtime"]

    def to_openai_function_schema(self) -> Dict[str, Any]:
        """
        Convert to OpenAI function calling format.

        Returns:
            Dict in OpenAI function schema format
        """
        properties = {}
        required = []

        for mapping in self.get_llm_parameters():
            param_name = mapping.llm_parameter_name or mapping.source_property

            # Build parameter schema
            param_schema = mapping.llm_schema or {"type": "string"}
            if mapping.llm_description:
                param_schema["description"] = mapping.llm_description

            properties[param_name] = param_schema

            if mapping.required:
                required.append(param_name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        }


class MappedStepTool(BaseModel):
    """
    A tool entry in the LLM step's tools array that wraps a step.

    This is the format stored in the graph JSON:
    {
        "type": "mapped_step",
        "definition": { ... ToolDefinition ... }
    }
    """

    type: Literal["mapped_step"] = "mapped_step"
    definition: ToolDefinition


class FunctionTool(BaseModel):
    """
    A tool entry that uses a direct function definition (OpenAI format).

    This allows users to define tools manually without mapping to steps:
    {
        "type": "function",
        "function": { ... OpenAI function schema ... }
    }
    """

    type: Literal["function"] = "function"
    function: Dict[str, Any] = Field(
        ...,
        description="OpenAI-style function definition"
    )
