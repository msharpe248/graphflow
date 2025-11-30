"""GraphFlow JSON Plugin - JSON manipulation steps."""

from .base import BaseJSONStep
from .core import JSONParseStep, JSONStringifyStep
from .advanced import (
    JSONPathStep,
    JSONMergeStep,
    JSONSchemaValidateStep,
    JSONGetStep,
    JSONSetStep,
    JSONKeysStep,
    JSONValuesStep,
)

# All step classes to be registered
STEPS = [
    # Core
    JSONParseStep,
    JSONStringifyStep,
    # Advanced
    JSONPathStep,
    JSONMergeStep,
    JSONSchemaValidateStep,
    JSONGetStep,
    JSONSetStep,
    JSONKeysStep,
    JSONValuesStep,
]

__all__ = [
    "BaseJSONStep",
    "JSONParseStep",
    "JSONStringifyStep",
    "JSONPathStep",
    "JSONMergeStep",
    "JSONSchemaValidateStep",
    "JSONGetStep",
    "JSONSetStep",
    "JSONKeysStep",
    "JSONValuesStep",
    "STEPS",
]
