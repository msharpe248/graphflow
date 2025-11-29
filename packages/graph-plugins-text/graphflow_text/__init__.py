"""GraphFlow Text Plugin - Text and string manipulation utilities."""

from .basic import (
    StringJoinStep,
    StringSplitStep,
    StringReplaceStep,
    StringReverseStep,
    StringRepeatStep,
)
from .formatting import (
    StringFormatStep,
    TextCaseStep,
    StringTrimStep,
    StringPadStep,
)
from .extraction import (
    SubstringStep,
    TextTruncateStep,
)
from .regex import (
    RegexMatchStep,
    RegexReplaceStep,
)

__version__ = "1.0.0"

__all__ = [
    # Basic operations
    "StringJoinStep",
    "StringSplitStep",
    "StringReplaceStep",
    "StringReverseStep",
    "StringRepeatStep",
    # Formatting
    "StringFormatStep",
    "TextCaseStep",
    "StringTrimStep",
    "StringPadStep",
    # Extraction
    "SubstringStep",
    "TextTruncateStep",
    # Regex
    "RegexMatchStep",
    "RegexReplaceStep",
]
