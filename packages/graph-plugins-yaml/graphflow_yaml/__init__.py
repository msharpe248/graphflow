"""GraphFlow YAML Plugin - YAML manipulation steps."""

from .base import BaseYAMLStep
from .core import YAMLParseStep, YAMLStringifyStep
from .advanced import (
    YAMLParseAllStep,
    YAMLStringifyAllStep,
    YAMLValidateStep,
    YAMLToJSONStep,
    JSONToYAMLStep,
    YAMLMergeStep,
    YAMLGetStep,
    YAMLSetStep,
)

# All step classes to be registered
STEPS = [
    # Core
    YAMLParseStep,
    YAMLStringifyStep,
    # Advanced
    YAMLParseAllStep,
    YAMLStringifyAllStep,
    YAMLValidateStep,
    YAMLToJSONStep,
    JSONToYAMLStep,
    YAMLMergeStep,
    YAMLGetStep,
    YAMLSetStep,
]

__all__ = [
    "BaseYAMLStep",
    "YAMLParseStep",
    "YAMLStringifyStep",
    "YAMLParseAllStep",
    "YAMLStringifyAllStep",
    "YAMLValidateStep",
    "YAMLToJSONStep",
    "JSONToYAMLStep",
    "YAMLMergeStep",
    "YAMLGetStep",
    "YAMLSetStep",
    "STEPS",
]
