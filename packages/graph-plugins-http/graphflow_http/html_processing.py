"""HTML processing step implementations."""
from typing import Any, Dict, List, Optional, Union
from bs4 import BeautifulSoup

from graphflow_core.memory import MemoryStore
from graphflow_core.steps.base import StepBase


class HTMLStripStep(StepBase):
    """Strip HTML tags from content step."""

    name = "HTML Strip"
    label = "HTML Strip"
    description = "Remove HTML tags from content, leaving only text"
    category = "http"

    @classmethod
    def get_type(cls) -> str:
        return "html-strip"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_key": {
                    "type": "string",
                    "description": "Memory key containing HTML content to strip"
                },
                "output_key": {
                    "type": "string",
                    "description": "Memory key to write plain text"
                },
                "separator": {
                    "type": "string",
                    "default": " ",
                    "description": "Separator to use between text elements (default: space)"
                },
                "strip_whitespace": {
                    "type": "boolean",
                    "default": True,
                    "description": "Remove excess whitespace from output"
                }
            },
            "required": ["input_key", "output_key"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "html": {
                    "type": "string",
                    "description": "HTML content to strip tags from (from input_key)"
                }
            },
            "required": ["html"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Plain text with HTML tags removed (written to output_key)"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute HTML strip."""
        html_content = memory.read(self.config["input_key"])
        separator = self.config.get("separator", " ")
        strip_whitespace = self.config.get("strip_whitespace", True)

        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(str(html_content), 'lxml')

        # Extract text
        text = soup.get_text(separator=separator)

        # Strip excess whitespace if requested
        if strip_whitespace:
            # Replace multiple whitespace with single space
            import re
            text = re.sub(r'\s+', ' ', text).strip()

        # Write to memory
        memory.write(self.config["output_key"], text)


class HTMLParseStep(StepBase):
    """Parse HTML and extract data using CSS selectors step."""

    name = "HTML Parse"
    label = "HTML Parse"
    description = "Extract data from HTML using CSS selectors"
    category = "http"

    @classmethod
    def get_type(cls) -> str:
        return "html-parse"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_key": {
                    "type": "string",
                    "description": "Memory key containing HTML content to parse"
                },
                "output_key": {
                    "type": "string",
                    "description": "Memory key to write extracted data"
                },
                "selectors": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "selector": {"type": "string"},
                            "attribute": {"type": "string"},
                            "multiple": {"type": "boolean"}
                        }
                    },
                    "description": "CSS selectors to extract data. Each key maps to a selector config."
                },
                "parser": {
                    "type": "string",
                    "enum": ["lxml", "html.parser", "html5lib"],
                    "default": "lxml",
                    "description": "HTML parser to use (default: lxml)"
                }
            },
            "required": ["input_key", "output_key", "selectors"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "html": {
                    "type": "string",
                    "description": "HTML content to parse (from input_key)"
                }
            },
            "required": ["html"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "data": {
                    "type": "object",
                    "description": "Extracted data as object with keys from selectors (written to output_key)"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute HTML parse."""
        html_content = memory.read(self.config["input_key"])
        selectors = self.config["selectors"]
        parser = self.config.get("parser", "lxml")

        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(str(html_content), parser)

        # Extract data using selectors
        extracted = {}
        for key, selector_config in selectors.items():
            css_selector = selector_config.get("selector")
            attribute = selector_config.get("attribute")
            multiple = selector_config.get("multiple", False)

            if not css_selector:
                continue

            if multiple:
                # Find all matching elements
                elements = soup.select(css_selector)
                if attribute:
                    # Extract attribute from each element
                    extracted[key] = [elem.get(attribute) for elem in elements if elem.get(attribute)]
                else:
                    # Extract text from each element
                    extracted[key] = [elem.get_text().strip() for elem in elements]
            else:
                # Find first matching element
                element = soup.select_one(css_selector)
                if element:
                    if attribute:
                        # Extract attribute value
                        extracted[key] = element.get(attribute)
                    else:
                        # Extract text content
                        extracted[key] = element.get_text().strip()
                else:
                    extracted[key] = None

        # Write to memory
        memory.write(self.config["output_key"], extracted)


class HTMLFindLinksStep(StepBase):
    """Find all links in HTML content step."""

    name = "HTML Find Links"
    label = "HTML Find Links"
    description = "Extract all links (URLs) from HTML content"
    category = "http"

    @classmethod
    def get_type(cls) -> str:
        return "html-find-links"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_key": {
                    "type": "string",
                    "description": "Memory key containing HTML content"
                },
                "output_key": {
                    "type": "string",
                    "description": "Memory key to write list of links"
                },
                "absolute_only": {
                    "type": "boolean",
                    "default": False,
                    "description": "Only return absolute URLs (starting with http/https)"
                },
                "unique": {
                    "type": "boolean",
                    "default": True,
                    "description": "Remove duplicate URLs"
                }
            },
            "required": ["input_key", "output_key"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "html": {
                    "type": "string",
                    "description": "HTML content to extract links from (from input_key)"
                }
            },
            "required": ["html"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "links": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of URLs found in HTML (written to output_key)"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute HTML find links."""
        html_content = memory.read(self.config["input_key"])
        absolute_only = self.config.get("absolute_only", False)
        unique = self.config.get("unique", True)

        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(str(html_content), 'lxml')

        # Find all <a> tags with href attribute
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']

            # Filter by absolute URLs if requested
            if absolute_only and not (href.startswith('http://') or href.startswith('https://')):
                continue

            links.append(href)

        # Remove duplicates if requested
        if unique:
            # Preserve order while removing duplicates
            seen = set()
            unique_links = []
            for link in links:
                if link not in seen:
                    seen.add(link)
                    unique_links.append(link)
            links = unique_links

        # Write to memory
        memory.write(self.config["output_key"], links)


class HTMLTableExtractStep(StepBase):
    """Extract data from HTML tables step."""

    name = "HTML Table Extract"
    label = "HTML Table Extract"
    description = "Extract data from HTML tables into structured format"
    category = "http"

    @classmethod
    def get_type(cls) -> str:
        return "html-table-extract"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input_key": {
                    "type": "string",
                    "description": "Memory key containing HTML content with tables"
                },
                "output_key": {
                    "type": "string",
                    "description": "Memory key to write extracted table data"
                },
                "table_selector": {
                    "type": "string",
                    "default": "table",
                    "description": "CSS selector to find table (default: 'table' finds first table)"
                },
                "headers": {
                    "type": "boolean",
                    "default": True,
                    "description": "First row contains headers (creates dict rows)"
                },
                "skip_rows": {
                    "type": "integer",
                    "default": 0,
                    "description": "Number of rows to skip at start"
                }
            },
            "required": ["input_key", "output_key"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "html": {
                    "type": "string",
                    "description": "HTML content with table (from input_key)"
                }
            },
            "required": ["html"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "table": {
                    "type": "array",
                    "description": "Table data as list of rows (dicts if headers=true, arrays if false)"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute HTML table extract."""
        html_content = memory.read(self.config["input_key"])
        table_selector = self.config.get("table_selector", "table")
        has_headers = self.config.get("headers", True)
        skip_rows = self.config.get("skip_rows", 0)

        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(str(html_content), 'lxml')

        # Find the table
        table = soup.select_one(table_selector)
        if not table:
            memory.write(self.config["output_key"], [])
            return

        # Extract all rows
        rows = table.find_all('tr')

        # Skip rows if requested
        if skip_rows > 0:
            rows = rows[skip_rows:]

        if not rows:
            memory.write(self.config["output_key"], [])
            return

        # Extract data
        table_data = []
        headers = None

        for i, row in enumerate(rows):
            # Get all cells (th or td)
            cells = row.find_all(['th', 'td'])
            cell_values = [cell.get_text().strip() for cell in cells]

            if has_headers and i == 0:
                # First row is headers
                headers = cell_values
            else:
                # Data row
                if has_headers and headers:
                    # Create dict with headers as keys
                    row_dict = {}
                    for j, value in enumerate(cell_values):
                        if j < len(headers):
                            row_dict[headers[j]] = value
                    table_data.append(row_dict)
                else:
                    # Just append array of values
                    table_data.append(cell_values)

        # Write to memory
        memory.write(self.config["output_key"], table_data)
