"""GraphFlow CSV Plugin - CSV manipulation steps."""

from .base import BaseCSVStep
from .core import (
    CSVParseStep,
    CSVStringifyStep,
    CSVGetHeadersStep,
    CSVToJSONStep,
    JSONToCSVStep,
)
from .advanced import (
    CSVFilterStep,
    CSVSelectColumnsStep,
    CSVSortStep,
    CSVGetColumnStep,
    CSVGetRowStep,
    CSVAddColumnStep,
    CSVRenameColumnsStep,
    CSVMergeStep,
    CSVGroupByStep,
)

# All step classes to be registered
STEPS = [
    # Core
    CSVParseStep,
    CSVStringifyStep,
    CSVGetHeadersStep,
    CSVToJSONStep,
    JSONToCSVStep,
    # Advanced
    CSVFilterStep,
    CSVSelectColumnsStep,
    CSVSortStep,
    CSVGetColumnStep,
    CSVGetRowStep,
    CSVAddColumnStep,
    CSVRenameColumnsStep,
    CSVMergeStep,
    CSVGroupByStep,
]

__all__ = [
    "BaseCSVStep",
    "CSVParseStep",
    "CSVStringifyStep",
    "CSVGetHeadersStep",
    "CSVToJSONStep",
    "JSONToCSVStep",
    "CSVFilterStep",
    "CSVSelectColumnsStep",
    "CSVSortStep",
    "CSVGetColumnStep",
    "CSVGetRowStep",
    "CSVAddColumnStep",
    "CSVRenameColumnsStep",
    "CSVMergeStep",
    "CSVGroupByStep",
    "STEPS",
]
