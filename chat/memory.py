"""
In-memory conversation history, keyed by session ID.

This is intentionally simple for now — a Python dictionary living in
server memory. It resets if the server restarts, and doesn't work
across multiple server instances. Fine for a demo; would need to move
to Redis or a database for real production use.
"""

from typing import TypedDict


class Turn(TypedDict):
    question: str
    answer: str


_sessions: dict[str, list[Turn]] = {}

MAX_HISTORY_TURNS = 5


def get_history(session_id: str) -> list[Turn]:
    return _sessions.get(session_id, [])


def add_turn(session_id: str, question: str, answer: str) -> None:
    history = _sessions.setdefault(session_id, [])
    history.append({"question": question, "answer": answer})
    if len(history) > MAX_HISTORY_TURNS:
        _sessions[session_id] = history[-MAX_HISTORY_TURNS:]