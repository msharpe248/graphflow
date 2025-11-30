"""Core CSV manipulation steps - parse and stringify."""
import csv
import io
import json
from typing import Any, Dict, List

from graphflow_core.memory import MemoryStore
from .base import BaseCSVStep


class CSVParseStep(BaseCSVStep):
    """Parse CSV string into list of rows."""

    name = "CSV Parse"
    label = "CSV Parse"
    description = "Parse a CSV string into a list of dictionaries (with headers) or list of lists"

    @classmethod
    def get_type(cls) -> str:
        return "csv.parse"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input CSV string using {memory.variable} syntax"
                },
                "has_header": {
                    "type": "boolean",
                    "default": True,
                    "description": "First row contains column headers"
                },
                "delimiter": {
                    "type": "string",
                    "default": ",",
                    "description": "Field delimiter character"
                },
                "quotechar": {
                    "type": "string",
                    "default": "\"",
                    "description": "Character used to quote fields"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "CSV string to parse"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "output": {
                    "type": "array",
                    "description": "Parsed rows (list of dicts if has_header, else list of lists)"
                },
                "headers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Column headers (if has_header is true)"
                },
                "row_count": {
                    "type": "integer",
                    "description": "Number of data rows"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        csv_string = self._get_input_string(memory, "input")
        has_header = self._get_config_value("has_header", True)
        delimiter = self._get_config_value("delimiter", ",")
        quotechar = self._get_config_value("quotechar", '"')

        reader = csv.reader(
            io.StringIO(csv_string),
            delimiter=delimiter,
            quotechar=quotechar
        )

        rows = list(reader)

        if has_header and rows:
            headers = rows[0]
            data_rows = [dict(zip(headers, row)) for row in rows[1:]]
            self._write_output(memory, "headers", headers)
        else:
            headers = []
            data_rows = rows

        self._write_output(memory, "output", data_rows)
        self._write_output(memory, "row_count", len(data_rows))


class CSVStringifyStep(BaseCSVStep):
    """Convert list of rows to CSV string."""

    name = "CSV Stringify"
    label = "CSV Stringify"
    description = "Convert a list of dictionaries or lists to a CSV string"

    @classmethod
    def get_type(cls) -> str:
        return "csv.stringify"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input rows using {memory.variable} syntax"
                },
                "headers": {
                    "type": "string",
                    "description": "Column headers using {memory.variable} syntax (optional, inferred from dicts)"
                },
                "delimiter": {
                    "type": "string",
                    "default": ",",
                    "description": "Field delimiter character"
                },
                "include_header": {
                    "type": "boolean",
                    "default": True,
                    "description": "Include header row in output"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "array",
                    "description": "List of rows (dicts or lists)"
                },
                "headers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Column headers (optional)"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "output": {
                    "type": "string",
                    "description": "CSV string"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        rows = self._get_input_value(memory, "input")
        delimiter = self._get_config_value("delimiter", ",")
        include_header = self._get_config_value("include_header", True)

        # Try to get headers from config
        headers = None
        if "headers" in self.config:
            headers_template = self.config["headers"]
            match = self._memory_pattern.search(headers_template)
            if match:
                namespace = match.group(1)
                field_key = match.group(2)
                headers = memory.read(f"{namespace}.{field_key}")

        output = io.StringIO()
        writer = csv.writer(output, delimiter=delimiter)

        if rows:
            # Determine if rows are dicts or lists
            first_row = rows[0]

            if isinstance(first_row, dict):
                # Infer headers from dict keys if not provided
                if headers is None:
                    headers = list(first_row.keys())

                if include_header:
                    writer.writerow(headers)

                for row in rows:
                    writer.writerow([row.get(h, "") for h in headers])
            else:
                # List of lists
                if include_header and headers:
                    writer.writerow(headers)

                for row in rows:
                    writer.writerow(row)

        self._write_output(memory, "output", output.getvalue())


class CSVGetHeadersStep(BaseCSVStep):
    """Get column headers from CSV."""

    name = "CSV Get Headers"
    label = "CSV Get Headers"
    description = "Extract column headers from a CSV string"

    @classmethod
    def get_type(cls) -> str:
        return "csv.get-headers"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input CSV string using {memory.variable} syntax"
                },
                "delimiter": {
                    "type": "string",
                    "default": ",",
                    "description": "Field delimiter character"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "CSV string"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "output": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Column headers"
                },
                "count": {
                    "type": "integer",
                    "description": "Number of columns"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        csv_string = self._get_input_string(memory, "input")
        delimiter = self._get_config_value("delimiter", ",")

        reader = csv.reader(io.StringIO(csv_string), delimiter=delimiter)
        headers = next(reader, [])

        self._write_output(memory, "output", headers)
        self._write_output(memory, "count", len(headers))


class CSVToJSONStep(BaseCSVStep):
    """Convert CSV to JSON array."""

    name = "CSV to JSON"
    label = "CSV to JSON"
    description = "Convert a CSV string to a JSON array of objects"

    @classmethod
    def get_type(cls) -> str:
        return "csv.to-json"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input CSV string using {memory.variable} syntax"
                },
                "delimiter": {
                    "type": "string",
                    "default": ",",
                    "description": "Field delimiter character"
                },
                "indent": {
                    "type": "integer",
                    "description": "JSON indentation (optional)"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "CSV string"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "output": {
                    "type": "string",
                    "description": "JSON array string"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        csv_string = self._get_input_string(memory, "input")
        delimiter = self._get_config_value("delimiter", ",")
        indent = self._get_config_value("indent")

        reader = csv.DictReader(io.StringIO(csv_string), delimiter=delimiter)
        rows = list(reader)

        json_string = json.dumps(rows, indent=indent)
        self._write_output(memory, "output", json_string)


class JSONToCSVStep(BaseCSVStep):
    """Convert JSON array to CSV."""

    name = "JSON to CSV"
    label = "JSON to CSV"
    description = "Convert a JSON array of objects to a CSV string"

    @classmethod
    def get_type(cls) -> str:
        return "csv.from-json"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input JSON array string using {memory.variable} syntax"
                },
                "delimiter": {
                    "type": "string",
                    "default": ",",
                    "description": "Field delimiter character"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "JSON array string"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "output": {
                    "type": "string",
                    "description": "CSV string"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        json_string = self._get_input_string(memory, "input")
        delimiter = self._get_config_value("delimiter", ",")

        try:
            rows = json.loads(json_string)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

        if not isinstance(rows, list):
            raise ValueError("JSON must be an array of objects")

        if not rows:
            self._write_output(memory, "output", "")
            return

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=rows[0].keys(),
            delimiter=delimiter
        )
        writer.writeheader()
        writer.writerows(rows)

        self._write_output(memory, "output", output.getvalue())
