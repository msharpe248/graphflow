"""Async executor for managing agent executions."""

import asyncio
import importlib.util
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import tempfile
import uuid

from graphflow_core.memory import MemoryStore
from graphflow_core.models import GraphDefinition
from graphflow_compiler import compile_graph


class AsyncExecutor:
    """
    Manages async execution of agents.

    Handles:
    - Compiling graphs on-the-fly
    - Running agents in background
    - Managing memory stores for active runs
    - Stopping/canceling runs
    """

    def __init__(self):
        """Initialize executor."""
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._memory_stores: Dict[str, MemoryStore] = {}
        self._temp_modules: Dict[str, str] = {}  # run_id -> module_path

    async def compile_and_run(
        self,
        run_id: str,
        graph: GraphDefinition,
        inputs: Dict[str, Any],
        framework: str = "pydantic_ai",
        on_complete: Optional[callable] = None,
        on_error: Optional[callable] = None
    ) -> None:
        """
        Compile graph and start execution in background.

        Args:
            run_id: Unique run identifier
            graph: Graph definition to compile and execute
            inputs: Input values for the agent
            framework: Framework to use for compilation
            on_complete: Callback for successful completion
            on_error: Callback for errors
        """
        # Compile graph to Python code
        code = compile_graph(graph, framework=framework, standalone=False)

        # Create temporary module
        temp_dir = tempfile.gettempdir()
        module_path = Path(temp_dir) / f"graphflow_agent_{run_id}.py"
        module_path.write_text(code)
        self._temp_modules[run_id] = str(module_path)

        # Create background task
        task = asyncio.create_task(
            self._execute_agent(
                run_id=run_id,
                module_path=module_path,
                inputs=inputs,
                on_complete=on_complete,
                on_error=on_error
            )
        )
        self._running_tasks[run_id] = task

    async def _execute_agent(
        self,
        run_id: str,
        module_path: Path,
        inputs: Dict[str, Any],
        on_complete: Optional[callable] = None,
        on_error: Optional[callable] = None
    ) -> None:
        """Execute agent and manage lifecycle."""
        try:
            # Load module dynamically
            spec = importlib.util.spec_from_file_location(f"agent_{run_id}", module_path)
            if not spec or not spec.loader:
                raise ImportError(f"Cannot load module from {module_path}")

            module = importlib.util.module_from_spec(spec)
            sys.modules[f"agent_{run_id}"] = module
            spec.loader.exec_module(module)

            # Create agent instance
            agent = module.GeneratedAgent()

            # Store memory reference for inspection
            self._memory_stores[run_id] = agent.memory

            # Run agent
            outputs = await agent.run(inputs)

            # Call completion callback
            if on_complete:
                await on_complete(run_id, outputs)

        except asyncio.CancelledError:
            # Task was cancelled (stopped by user)
            if on_error:
                await on_error(run_id, "Run was stopped by user")
            raise

        except Exception as e:
            # Error during execution
            if on_error:
                await on_error(run_id, str(e))
            raise

        finally:
            # Cleanup task reference
            if run_id in self._running_tasks:
                del self._running_tasks[run_id]

            # Cleanup module
            if f"agent_{run_id}" in sys.modules:
                del sys.modules[f"agent_{run_id}"]

    def get_memory(self, run_id: str) -> Optional[MemoryStore]:
        """
        Get memory store for a run.

        Args:
            run_id: Run identifier

        Returns:
            Memory store if run exists, None otherwise
        """
        return self._memory_stores.get(run_id)

    def get_memory_state(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get memory state as dictionary.

        Args:
            run_id: Run identifier

        Returns:
            Memory state dict or None
        """
        memory = self.get_memory(run_id)
        if memory:
            return memory.to_dict()
        return None

    def stop_run(self, run_id: str) -> bool:
        """
        Stop a running agent.

        Args:
            run_id: Run identifier

        Returns:
            True if run was stopped, False if not found or already completed
        """
        if run_id in self._running_tasks:
            task = self._running_tasks[run_id]
            if not task.done():
                task.cancel()
                return True
        return False

    def release_memory(self, run_id: str) -> bool:
        """
        Release memory for a run.

        Args:
            run_id: Run identifier

        Returns:
            True if memory was released, False if not found
        """
        if run_id in self._memory_stores:
            del self._memory_stores[run_id]

            # Also cleanup temp module file
            if run_id in self._temp_modules:
                try:
                    Path(self._temp_modules[run_id]).unlink(missing_ok=True)
                except Exception:
                    pass
                del self._temp_modules[run_id]

            return True
        return False

    def is_running(self, run_id: str) -> bool:
        """Check if a run is currently executing."""
        if run_id in self._running_tasks:
            task = self._running_tasks[run_id]
            return not task.done()
        return False

    def get_active_runs(self) -> list[str]:
        """Get list of active run IDs."""
        return [
            run_id
            for run_id, task in self._running_tasks.items()
            if not task.done()
        ]

    async def shutdown(self):
        """Shutdown executor and cancel all running tasks."""
        # Cancel all running tasks
        for run_id in list(self._running_tasks.keys()):
            self.stop_run(run_id)

        # Wait for all tasks to complete
        if self._running_tasks:
            await asyncio.gather(*self._running_tasks.values(), return_exceptions=True)

        # Cleanup all memory stores
        for run_id in list(self._memory_stores.keys()):
            self.release_memory(run_id)
