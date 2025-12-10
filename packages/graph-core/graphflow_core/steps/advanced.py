"""Advanced step types - loops, database queries, and more."""

from typing import Any, Dict, List
from graphflow_core.steps.base import StepBase
from graphflow_core.steps.registry import StepRegistry
from graphflow_core.steps.memory_mixin import MemoryMixin
from graphflow_core.memory.store import MemoryStore


@StepRegistry.register(
    category="control",
    description="Iterate over a collection and execute sub-operations"
)
class LoopStep(StepBase):
    """
    Loop step - iterate over a collection.

    Config:
        collection_key: str - Memory key containing collection to iterate
        item_key: str - Memory key to write current item
        index_key: str - Memory key to write current index (optional)
        max_iterations: int - Maximum iterations (safety limit, default: 1000)

    Note: The actual loop body execution is handled by the execution engine
    which processes the subgraph defined within the loop.
    """

    can_be_tool = False
    tool_ineligible_reason = "Control flow steps cannot be used as tools"

    @classmethod
    def get_type(cls) -> str:
        return "loop"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "collection_key": {
                    "type": "string",
                    "description": "Memory key containing collection to iterate over"
                },
                "item_key": {
                    "type": "string",
                    "description": "Memory key to write current item during iteration"
                },
                "index_key": {
                    "type": "string",
                    "description": "Memory key to write current index (optional)"
                },
                "max_iterations": {
                    "type": "integer",
                    "minimum": 1,
                    "default": 1000,
                    "description": "Maximum number of iterations (safety limit)"
                },
                "results_key": {
                    "type": "string",
                    "description": "Memory key to collect results from each iteration"
                }
            },
            "required": ["collection_key", "item_key"]
        }

    async def execute(self, memory: MemoryStore) -> None:
        """
        Execute loop iteration.

        This is a simplified version for testing. Full implementation
        requires execution engine support for loop subgraphs.
        """
        collection_key = self.config["collection_key"]
        item_key = self.config["item_key"]
        index_key = self.config.get("index_key")
        max_iterations = self.config.get("max_iterations", 1000)
        results_key = self.config.get("results_key")

        # Get collection
        try:
            collection = memory.read(collection_key)
        except KeyError:
            raise ValueError(f"LoopStep {self.id}: collection_key '{collection_key}' not found")

        if not isinstance(collection, (list, tuple)):
            raise ValueError(f"LoopStep {self.id}: collection must be list or tuple")

        # Safety check
        if len(collection) > max_iterations:
            raise ValueError(
                f"LoopStep {self.id}: collection size ({len(collection)}) "
                f"exceeds max_iterations ({max_iterations})"
            )

        # Iterate (simplified - real implementation would execute subgraph)
        results = []
        for idx, item in enumerate(collection):
            # Write current item and index to memory
            memory.write(item_key, item)
            if index_key:
                memory.write(index_key, idx)

            # In full implementation, would execute loop body subgraph here
            # For now, just collect items
            results.append(item)

        # Write results if configured
        if results_key:
            memory.write(results_key, results)


@StepRegistry.register(
    category="data",
    description="Execute database query using SQL"
)
class DBQueryStep(StepBase, MemoryMixin):
    """
    Database query step - execute SQL queries.

    Config:
        connection: str or Dict - Database connection info
            - String: connection string (e.g., "postgresql://user:pass@host/db")
            - Dict: {driver, host, port, database, user, password_secret}
        query: str - SQL query template (supports {{variable}} syntax for legacy)
        params: Dict - Query parameters (for parameterized queries)
        fetch_mode: str - "all", "one", or "none" (default: "all")
        results_key: str - Memory key to write query results
        row_count_key: str - Memory key to write affected row count (optional)

    Example:
        {
            "connection": "postgresql://localhost/mydb",
            "query": "SELECT * FROM users WHERE age > {{min_age}}",
            "fetch_mode": "all",
            "results_key": "users"
        }

    Inherits from MemoryMixin for centralized template resolution.
    Supports legacy {{variable}} syntax for backwards compatibility.
    """

    can_be_tool = True  # Database queries can be wrapped as LLM tools

    @classmethod
    def get_type(cls) -> str:
        return "db_query"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "connection": {
                    "oneOf": [
                        {"type": "string"},
                        {
                            "type": "object",
                            "properties": {
                                "driver": {"type": "string"},
                                "host": {"type": "string"},
                                "port": {"type": "integer"},
                                "database": {"type": "string"},
                                "user": {"type": "string"},
                                "password_secret": {"type": "string"}
                            }
                        }
                    ],
                    "description": "Database connection info"
                },
                "query": {
                    "type": "string",
                    "description": "SQL query template (supports {{variable}} syntax)"
                },
                "params": {
                    "type": "object",
                    "description": "Query parameters for parameterized queries"
                },
                "fetch_mode": {
                    "type": "string",
                    "enum": ["all", "one", "none"],
                    "default": "all",
                    "description": "Fetch mode: all rows, one row, or none"
                },
                "results_key": {
                    "type": "string",
                    "description": "Memory key to write query results"
                },
                "row_count_key": {
                    "type": "string",
                    "description": "Memory key to write affected row count"
                }
            },
            "required": ["connection", "query", "results_key"]
        }

    async def execute(self, memory: MemoryStore) -> None:
        """
        Execute database query.

        This is a placeholder implementation. Real implementation would:
        1. Establish database connection
        2. Render query template with memory values
        3. Execute query
        4. Fetch and write results to memory
        """
        query = self.config["query"]
        fetch_mode = self.config.get("fetch_mode", "all")
        results_key = self.config["results_key"]
        row_count_key = self.config.get("row_count_key")

        # Render query template using centralized resolver with legacy support
        rendered_query = self._resolve(query, memory, allow_legacy=True)

        # Mock execution
        # In real implementation, would use SQLAlchemy or database driver
        mock_results = [
            {"id": 1, "name": "Mock Result 1"},
            {"id": 2, "name": "Mock Result 2"}
        ]

        if fetch_mode == "one":
            result = mock_results[0] if mock_results else None
        elif fetch_mode == "none":
            result = None
        else:  # all
            result = mock_results

        # Write results
        memory.write(results_key, result)

        if row_count_key:
            memory.write(row_count_key, len(mock_results) if mock_results else 0)
