"""GraphFlow HTTP Plugin - HTTP client and web utilities."""

from .request import (
    HTTPGetStep,
    HTTPPostStep,
    HTTPPutStep,
    HTTPPatchStep,
    HTTPDeleteStep,
)

from .url_utils import (
    URLEscapeStep,
    URLUnescapeStep,
    URLBuildStep,
    URLParseStep,
)

from .data_transforms import (
    Base64EncodeStep,
    Base64DecodeStep,
)

from .html_processing import (
    HTMLStripStep,
    HTMLParseStep,
    HTMLFindLinksStep,
    HTMLTableExtractStep,
)

__version__ = "1.0.0"


__all__ = [
    # HTTP Request Steps
    'HTTPGetStep',
    'HTTPPostStep',
    'HTTPPutStep',
    'HTTPPatchStep',
    'HTTPDeleteStep',
    # URL Utility Steps
    'URLEscapeStep',
    'URLUnescapeStep',
    'URLBuildStep',
    'URLParseStep',
    # Data Transformation Steps
    'Base64EncodeStep',
    'Base64DecodeStep',
    # HTML Processing Steps
    'HTMLStripStep',
    'HTMLParseStep',
    'HTMLFindLinksStep',
    'HTMLTableExtractStep',
]
