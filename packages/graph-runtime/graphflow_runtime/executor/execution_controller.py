"""Execution controller for debugger support."""

import asyncio
from typing import Dict, Set, Optional, Callable
from enum import Enum
from datetime import datetime


class ExecutionState(Enum):
    """Execution state for debugger."""
    RUNNING = "running"
    PAUSED = "paused"
    STEPPING = "stepping"
    STOPPED = "stopped"


class ExecutionController:
    """
    Controls execution flow for debugging.

    Manages:
    - Pause/resume/step commands
    - Breakpoints (dynamic)
    - Execution state
    - Step execution counts (for loops)
    - Event callbacks for WebSocket notifications
    """

    def __init__(self, run_id: str, initial_breakpoints: Optional[Set[str]] = None):
        """
        Initialize execution controller.

        Args:
            run_id: Run identifier
            initial_breakpoints: Initial set of breakpoint step IDs
        """
        self.run_id = run_id
        self.state = ExecutionState.PAUSED  # Start paused in debug mode
        self.current_step_id: Optional[str] = None
        self.breakpoints: Set[str] = initial_breakpoints or set()
        self.step_execution_counts: Dict[str, int] = {}

        # Event for controlling execution flow
        self._resume_event = asyncio.Event()
        # Don't set initially - start paused (user must click Resume or Step)

        # Callbacks for events (WebSocket notifications)
        self.on_step_started: Optional[Callable] = None
        self.on_step_completed: Optional[Callable] = None
        self.on_paused: Optional[Callable] = None
        self.on_resumed: Optional[Callable] = None
        self.on_breakpoint_added: Optional[Callable] = None
        self.on_breakpoint_removed: Optional[Callable] = None

        # Lock for thread safety
        self._lock = asyncio.Lock()

    async def wait_if_paused(self, step_id: str) -> None:
        """
        Check if should pause before executing step.

        This is called before each step execution. It will:
        1. Check if there's a breakpoint on this step (before)
        2. Check if in stepping mode
        3. Wait if paused

        Args:
            step_id: Step ID about to be executed
        """
        needs_to_wait = False

        async with self._lock:
            self.current_step_id = step_id
            # Note: We don't increment execution count here anymore - it happens in step_completed

            # Emit step started event
            if self.on_step_started:
                await self.on_step_started({
                    'type': 'step_started',
                    'step_id': step_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'execution_count': self.step_execution_counts.get(step_id, 0)  # Current count, not incremented yet
                })

            # Check if should pause (before breakpoint)
            should_pause = False
            pause_reason = None

            if step_id in self.breakpoints:  # Before breakpoint
                should_pause = True
                pause_reason = 'breakpoint_before'
            elif self.state == ExecutionState.STEPPING:
                should_pause = True
                pause_reason = 'step'

            if should_pause:
                self.state = ExecutionState.PAUSED
                self._resume_event.clear()
                needs_to_wait = True

                # Emit paused event
                if self.on_paused:
                    await self.on_paused({
                        'type': 'paused',
                        'step_id': step_id,
                        'timestamp': datetime.utcnow().isoformat(),
                        'reason': pause_reason
                    })
            # Also wait if we're in a paused/stepping state (from initial debug start)
            elif self.state in (ExecutionState.PAUSED, ExecutionState.STEPPING):
                needs_to_wait = True

        # Wait for resume signal only if needed (outside lock to allow other operations)
        if needs_to_wait:
            await self._resume_event.wait()

    async def step_completed(self, step_id: str) -> None:
        """
        Notify that a step has completed execution.
        Increment execution count and check for after breakpoints or stepping.

        Args:
            step_id: Step ID that completed
        """
        async with self._lock:
            # Increment execution count NOW (after step completes)
            self.step_execution_counts[step_id] = self.step_execution_counts.get(step_id, 0) + 1

            # Emit step completed event
            if self.on_step_completed:
                await self.on_step_completed({
                    'type': 'step_completed',
                    'step_id': step_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'execution_count': self.step_execution_counts[step_id]
                })

            # Check if should pause
            should_pause = False
            pause_reason = None

            # After breakpoint
            after_breakpoint_id = f"{step_id}:after"
            if after_breakpoint_id in self.breakpoints:
                should_pause = True
                pause_reason = 'breakpoint_after'
            # OR if we're in stepping mode, pause after completing the step
            elif self.state == ExecutionState.STEPPING:
                should_pause = True
                pause_reason = 'step'

            if should_pause:
                self.state = ExecutionState.PAUSED
                self._resume_event.clear()

                # Emit paused event
                if self.on_paused:
                    await self.on_paused({
                        'type': 'paused',
                        'step_id': step_id,
                        'timestamp': datetime.utcnow().isoformat(),
                        'reason': pause_reason
                    })

        # Wait for resume if we should pause (outside lock)
        if should_pause:
            await self._resume_event.wait()

    async def pause(self) -> bool:
        """
        Pause execution.

        Returns:
            True if paused, False if already paused or stopped
        """
        async with self._lock:
            if self.state == ExecutionState.RUNNING:
                self.state = ExecutionState.PAUSED
                self._resume_event.clear()

                if self.on_paused:
                    await self.on_paused({
                        'type': 'paused',
                        'step_id': self.current_step_id,
                        'timestamp': datetime.utcnow().isoformat(),
                        'reason': 'user'
                    })

                return True
            return False

    async def resume(self) -> bool:
        """
        Resume execution (run to next breakpoint or completion).

        Returns:
            True if resumed, False if already running or stopped
        """
        async with self._lock:
            if self.state == ExecutionState.PAUSED or self.state == ExecutionState.STEPPING:
                self.state = ExecutionState.RUNNING
                self._resume_event.set()

                if self.on_resumed:
                    await self.on_resumed({
                        'type': 'resumed',
                        'timestamp': datetime.utcnow().isoformat()
                    })

                return True
            return False

    async def step(self) -> bool:
        """
        Execute one step then pause.

        Returns:
            True if stepped, False if stopped
        """
        async with self._lock:
            if self.state != ExecutionState.STOPPED:
                self.state = ExecutionState.STEPPING
                self._resume_event.set()

                if self.on_resumed:
                    await self.on_resumed({
                        'type': 'resumed',
                        'timestamp': datetime.utcnow().isoformat()
                    })

                return True
            return False

    async def stop(self) -> None:
        """Stop execution (no resume possible)."""
        async with self._lock:
            self.state = ExecutionState.STOPPED
            self._resume_event.set()  # Unblock any waiting

    async def set_breakpoint(self, step_id: str) -> None:
        """
        Add a breakpoint on a step.

        Args:
            step_id: Step ID to break on
        """
        async with self._lock:
            self.breakpoints.add(step_id)

            if self.on_breakpoint_added:
                await self.on_breakpoint_added({
                    'type': 'breakpoint_added',
                    'step_id': step_id,
                    'timestamp': datetime.utcnow().isoformat()
                })

    async def clear_breakpoint(self, step_id: str) -> bool:
        """
        Remove a breakpoint from a step.

        Args:
            step_id: Step ID to remove breakpoint from

        Returns:
            True if breakpoint was removed, False if didn't exist
        """
        async with self._lock:
            if step_id in self.breakpoints:
                self.breakpoints.remove(step_id)

                if self.on_breakpoint_removed:
                    await self.on_breakpoint_removed({
                        'type': 'breakpoint_removed',
                        'step_id': step_id,
                        'timestamp': datetime.utcnow().isoformat()
                    })

                return True
            return False

    def get_execution_count(self, step_id: str) -> int:
        """
        Get execution count for a step.

        Args:
            step_id: Step ID

        Returns:
            Number of times step has executed
        """
        return self.step_execution_counts.get(step_id, 0)

    def get_state(self) -> Dict:
        """
        Get current debug state.

        Returns:
            Dict with current state, step, breakpoints, counts
        """
        return {
            'current_step_id': self.current_step_id,
            'breakpoints': list(self.breakpoints),
            'step_execution_counts': self.step_execution_counts.copy(),
            'status': self.state.value,
        }
