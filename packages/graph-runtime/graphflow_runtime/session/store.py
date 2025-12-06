"""Simple in-memory session store for LLM conversation history."""
from typing import Dict, List, Any
from collections import defaultdict

# Storage: {session_id: {step_id: [messages]}}
_sessions: Dict[str, Dict[str, List[Any]]] = defaultdict(lambda: defaultdict(list))


def get_history(session_id: str, step_id: str) -> List[Any]:
    """Get history for a specific step in a session."""
    if session_id not in _sessions:
        return []
    if step_id not in _sessions[session_id]:
        return []
    return _sessions[session_id][step_id].copy()


def set_history(session_id: str, step_id: str, messages: List[Any]) -> None:
    """Replace history for a specific step."""
    _sessions[session_id][step_id] = messages


def clear_session(session_id: str) -> bool:
    """Clear all history for a session. Returns True if session existed."""
    if session_id in _sessions:
        del _sessions[session_id]
        return True
    return False


def list_sessions() -> List[str]:
    """List all active session IDs."""
    return list(_sessions.keys())


def session_exists(session_id: str) -> bool:
    """Check if a session exists."""
    return session_id in _sessions


def get_session_history(session_id: str) -> dict:
    """
    Get all history for a session, organized by step ID.

    Returns a dictionary mapping step_id -> list of messages.
    Each message is serialized to a dict for JSON compatibility.
    """
    if session_id not in _sessions:
        return {}

    result = {}
    for step_id, messages in _sessions[session_id].items():
        # Serialize messages to dicts for JSON response
        serialized_messages = []
        for msg in messages:
            if hasattr(msg, 'model_dump'):
                # Pydantic model
                serialized_messages.append(msg.model_dump())
            elif hasattr(msg, 'dict'):
                # Older Pydantic model
                serialized_messages.append(msg.dict())
            elif isinstance(msg, dict):
                serialized_messages.append(msg)
            else:
                # Fallback: convert to string representation
                serialized_messages.append({"content": str(msg), "type": type(msg).__name__})
        result[step_id] = serialized_messages

    return result
