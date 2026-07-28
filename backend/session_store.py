"""
session_store.py
-----------------
Holds the IN-PROGRESS draft (and required completeness state) for each
active Copilot chat session, keyed by session_id.

This is a plain in-memory dict - fine for a demo/single-process MVP, but
it means drafts are lost on server restart and won't work across multiple
backend instances. In production this would be swapped for Redis (or a
"draft_complaints" DB table with a TTL) - the FastAPI routes only talk to
the three functions below, so that swap wouldn't touch any other file.
"""
from typing import Optional

_sessions: dict[str, dict] = {}

REQUIRED_FOR_READY = ["product_name", "batch_number", "complaint_description"]


def get_draft(session_id: str) -> dict:
    return _sessions.setdefault(session_id, {})


def save_draft(session_id: str, draft: dict) -> None:
    _sessions[session_id] = draft


def clear_draft(session_id: str) -> None:
    _sessions.pop(session_id, None)


def compute_status(draft: dict) -> str:
    """Mirrors the demo's badge: 'Pending Triage' until the core required
    fields are present, then 'Ready to Commit'."""
    if all(draft.get(f) for f in REQUIRED_FOR_READY):
        return "ready_to_commit"
    return "pending_triage"
