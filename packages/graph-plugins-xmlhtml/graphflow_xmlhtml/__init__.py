"""GraphFlow XML & HTML Plugin - XML parsing and HTML manipulation utilities."""

from .html_core import (
    HTMLStripStep,
    HTMLParseStep,
    HTMLFindLinksStep,
    HTMLTableExtractStep,
)

from .xml_steps import (
    XMLParseStep,
    XMLToJSONStep,
    JSONToXMLStep,
)

from .html_extraction import (
    HTMLSelectAllStep,
    HTMLAttributeExtractStep,
    HTMLFormExtractStep,
    HTMLMetaExtractStep,
)

from .html_transform import (
    HTMLToMarkdownStep,
    HTMLCleanStep,
    XPathStep,
)

__version__ = "1.0.0"


__all__ = [
    # Core HTML Steps
    'HTMLStripStep',
    'HTMLParseStep',
    'HTMLFindLinksStep',
    'HTMLTableExtractStep',
    # XML Steps
    'XMLParseStep',
    'XMLToJSONStep',
    'JSONToXMLStep',
    # HTML Extraction Steps
    'HTMLSelectAllStep',
    'HTMLAttributeExtractStep',
    'HTMLFormExtractStep',
    'HTMLMetaExtractStep',
    # HTML Transform Steps
    'HTMLToMarkdownStep',
    'HTMLCleanStep',
    'XPathStep',
]
