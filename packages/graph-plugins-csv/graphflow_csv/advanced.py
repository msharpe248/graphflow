"""Advanced CSV manipulation steps - filter, select, sort, transform."""
import csv
import io
import copy
import operator
from typing import Any, Dict, List

from graphflow_core.memory import MemoryStore
from .base import BaseCSVStep


class CSVFilterStep(BaseCSVStep):
    """Filter CSV rows based on conditions."""

    name = "CSV Filter"
    label = "CSV Filter"
    description = "Filter rows based on column value conditions"

    @classmethod
    def get_type(cls) -> str:
        return "csv.filter"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input rows (list of dicts) using {memory.variable} syntax"
                },
                "column": {
                    "type": "string",
                    "description": "Column name to filter on"
                },
                "operator": {
                    "type": "string",
                    "enum": ["eq", "ne", "gt", "gte", "lt", "lte", "contains", "startswith", "endswith"],
                    "default": "eq",
                    "description": "Comparison operator"
                },
                "value": {
                    "description": "Value to compare against"
                }
            },
            "required": ["input", "column", "value"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "array",
                    "description": "List of row dictionaries"
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
                    "description": "Filtered rows"
                },
                "count": {
                    "type": "integer",
                    "description": "Number of matching rows"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        rows = self._get_input_value(memory, "input")
        column = self._get_config_value("column")
        op = self._get_config_value("operator", "eq")
        value = self._get_config_value("value")

        ops = {
            "eq": lambda a, b: str(a) == str(b),
            "ne": lambda a, b: str(a) != str(b),
            "gt": lambda a, b: float(a) > float(b),
            "gte": lambda a, b: float(a) >= float(b),
            "lt": lambda a, b: float(a) < float(b),
            "lte": lambda a, b: float(a) <= float(b),
            "contains": lambda a, b: str(b) in str(a),
            "startswith": lambda a, b: str(a).startswith(str(b)),
            "endswith": lambda a, b: str(a).endswith(str(b)),
        }

        compare = ops.get(op, ops["eq"])

        filtered = []
        for row in rows:
            try:
                if column in row and compare(row[column], value):
                    filtered.append(row)
            except (ValueError, TypeError):
                pass

        self._write_output(memory, "output", filtered)
        self._write_output(memory, "count", len(filtered))


class CSVSelectColumnsStep(BaseCSVStep):
    """Select specific columns from CSV rows."""

    name = "CSV Select Columns"
    label = "CSV Select Columns"
    description = "Select and optionally reorder specific columns"

    @classmethod
    def get_type(cls) -> str:
        return "csv.select-columns"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input rows using {memory.variable} syntax"
                },
                "columns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of column names to select"
                }
            },
            "required": ["input", "columns"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "array",
                    "description": "List of row dictionaries"
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
                    "description": "Rows with selected columns only"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        rows = self._get_input_value(memory, "input")
        columns = self._get_config_value("columns", [])

        result = []
        for row in rows:
            new_row = {col: row.get(col) for col in columns}
            result.append(new_row)

        self._write_output(memory, "output", result)


class CSVSortStep(BaseCSVStep):
    """Sort CSV rows by column(s)."""

    name = "CSV Sort"
    label = "CSV Sort"
    description = "Sort rows by one or more columns"

    @classmethod
    def get_type(cls) -> str:
        return "csv.sort"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input rows using {memory.variable} syntax"
                },
                "column": {
                    "type": "string",
                    "description": "Column name to sort by"
                },
                "descending": {
                    "type": "boolean",
                    "default": False,
                    "description": "Sort in descending order"
                },
                "numeric": {
                    "type": "boolean",
                    "default": False,
                    "description": "Treat values as numbers"
                }
            },
            "required": ["input", "column"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "array",
                    "description": "List of row dictionaries"
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
                    "description": "Sorted rows"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        rows = self._get_input_value(memory, "input")
        column = self._get_config_value("column")
        descending = self._get_config_value("descending", False)
        numeric = self._get_config_value("numeric", False)

        def sort_key(row):
            val = row.get(column, "")
            if numeric:
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return 0
            return str(val)

        sorted_rows = sorted(rows, key=sort_key, reverse=descending)
        self._write_output(memory, "output", sorted_rows)


class CSVGetColumnStep(BaseCSVStep):
    """Extract a single column as an array."""

    name = "CSV Get Column"
    label = "CSV Get Column"
    description = "Extract all values from a single column"

    @classmethod
    def get_type(cls) -> str:
        return "csv.get-column"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input rows using {memory.variable} syntax"
                },
                "column": {
                    "type": "string",
                    "description": "Column name to extract"
                },
                "unique": {
                    "type": "boolean",
                    "default": False,
                    "description": "Return only unique values"
                }
            },
            "required": ["input", "column"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "array",
                    "description": "List of row dictionaries"
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
                    "description": "Column values"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        rows = self._get_input_value(memory, "input")
        column = self._get_config_value("column")
        unique = self._get_config_value("unique", False)

        values = [row.get(column) for row in rows]

        if unique:
            seen = set()
            unique_values = []
            for v in values:
                key = str(v)
                if key not in seen:
                    seen.add(key)
                    unique_values.append(v)
            values = unique_values

        self._write_output(memory, "output", values)


class CSVGetRowStep(BaseCSVStep):
    """Get a specific row by index."""

    name = "CSV Get Row"
    label = "CSV Get Row"
    description = "Get a specific row by its index"

    @classmethod
    def get_type(cls) -> str:
        return "csv.get-row"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input rows using {memory.variable} syntax"
                },
                "index": {
                    "type": "integer",
                    "description": "Row index (0-based, negative for from end)"
                }
            },
            "required": ["input", "index"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "array",
                    "description": "List of row dictionaries"
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
                    "type": "object",
                    "description": "Row at the specified index"
                },
                "found": {
                    "type": "boolean",
                    "description": "Whether the row was found"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        rows = self._get_input_value(memory, "input")
        index = self._get_config_value("index", 0)

        try:
            row = rows[index]
            found = True
        except IndexError:
            row = None
            found = False

        self._write_output(memory, "output", row)
        self._write_output(memory, "found", found)


class CSVAddColumnStep(BaseCSVStep):
    """Add a new column to CSV rows."""

    name = "CSV Add Column"
    label = "CSV Add Column"
    description = "Add a new column with a constant value or computed from other columns"

    @classmethod
    def get_type(cls) -> str:
        return "csv.add-column"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input rows using {memory.variable} syntax"
                },
                "column": {
                    "type": "string",
                    "description": "Name for the new column"
                },
                "value": {
                    "description": "Constant value for all rows"
                },
                "from_column": {
                    "type": "string",
                    "description": "Copy values from another column (alternative to value)"
                }
            },
            "required": ["input", "column"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "array",
                    "description": "List of row dictionaries"
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
                    "description": "Rows with the new column"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        rows = self._get_input_value(memory, "input")
        column = self._get_config_value("column")
        value = self._get_config_value("value")
        from_column = self._get_config_value("from_column")

        result = []
        for row in rows:
            new_row = copy.copy(row)
            if from_column:
                new_row[column] = row.get(from_column)
            else:
                new_row[column] = value
            result.append(new_row)

        self._write_output(memory, "output", result)


class CSVRenameColumnsStep(BaseCSVStep):
    """Rename columns in CSV rows."""

    name = "CSV Rename Columns"
    label = "CSV Rename Columns"
    description = "Rename one or more columns"

    @classmethod
    def get_type(cls) -> str:
        return "csv.rename-columns"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input rows using {memory.variable} syntax"
                },
                "mapping": {
                    "type": "object",
                    "description": "Object mapping old names to new names",
                    "additionalProperties": {"type": "string"}
                }
            },
            "required": ["input", "mapping"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "array",
                    "description": "List of row dictionaries"
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
                    "description": "Rows with renamed columns"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        rows = self._get_input_value(memory, "input")
        mapping = self._get_config_value("mapping", {})

        result = []
        for row in rows:
            new_row = {}
            for key, value in row.items():
                new_key = mapping.get(key, key)
                new_row[new_key] = value
            result.append(new_row)

        self._write_output(memory, "output", result)


class CSVMergeStep(BaseCSVStep):
    """Merge two CSV datasets."""

    name = "CSV Merge"
    label = "CSV Merge"
    description = "Merge two CSV datasets by appending rows or joining on a column"

    @classmethod
    def get_type(cls) -> str:
        return "csv.merge"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "left": {
                    "type": "string",
                    "description": "First dataset using {memory.variable} syntax"
                },
                "right": {
                    "type": "string",
                    "description": "Second dataset using {memory.variable} syntax"
                },
                "mode": {
                    "type": "string",
                    "enum": ["append", "join"],
                    "default": "append",
                    "description": "Merge mode: append rows or join on column"
                },
                "on": {
                    "type": "string",
                    "description": "Column to join on (required for join mode)"
                },
                "join_type": {
                    "type": "string",
                    "enum": ["inner", "left", "right", "outer"],
                    "default": "inner",
                    "description": "Type of join (for join mode)"
                }
            },
            "required": ["left", "right"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "left": {
                    "type": "array",
                    "description": "First dataset"
                },
                "right": {
                    "type": "array",
                    "description": "Second dataset"
                }
            },
            "required": ["left", "right"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "output": {
                    "type": "array",
                    "description": "Merged dataset"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        left = self._get_input_value(memory, "left")
        right = self._get_input_value(memory, "right")
        mode = self._get_config_value("mode", "append")
        on_column = self._get_config_value("on")
        join_type = self._get_config_value("join_type", "inner")

        if mode == "append":
            result = left + right
        elif mode == "join":
            if not on_column:
                raise ValueError("'on' column is required for join mode")

            # Build index of right table
            right_index = {}
            for row in right:
                key = row.get(on_column)
                if key not in right_index:
                    right_index[key] = []
                right_index[key].append(row)

            result = []

            # Process left rows
            matched_keys = set()
            for left_row in left:
                key = left_row.get(on_column)
                if key in right_index:
                    matched_keys.add(key)
                    for right_row in right_index[key]:
                        merged = {**left_row, **right_row}
                        result.append(merged)
                elif join_type in ("left", "outer"):
                    result.append(left_row)

            # Add unmatched right rows for right/outer joins
            if join_type in ("right", "outer"):
                for row in right:
                    key = row.get(on_column)
                    if key not in matched_keys:
                        result.append(row)
        else:
            result = left

        self._write_output(memory, "output", result)


class CSVGroupByStep(BaseCSVStep):
    """Group CSV rows by a column."""

    name = "CSV Group By"
    label = "CSV Group By"
    description = "Group rows by a column value"

    @classmethod
    def get_type(cls) -> str:
        return "csv.group-by"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input rows using {memory.variable} syntax"
                },
                "column": {
                    "type": "string",
                    "description": "Column to group by"
                }
            },
            "required": ["input", "column"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "array",
                    "description": "List of row dictionaries"
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
                    "type": "object",
                    "description": "Object with group keys and their rows"
                },
                "keys": {
                    "type": "array",
                    "description": "List of unique group keys"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        rows = self._get_input_value(memory, "input")
        column = self._get_config_value("column")

        groups = {}
        for row in rows:
            key = str(row.get(column, ""))
            if key not in groups:
                groups[key] = []
            groups[key].append(row)

        self._write_output(memory, "output", groups)
        self._write_output(memory, "keys", list(groups.keys()))
