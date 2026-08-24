import os
import shutil
import uuid
from dataclasses import dataclass, field

from . import config


@dataclass
class SessionState:
    session_id: str
    tmp_dir: str
    chunk_count: int = 0
    tail_words: str = ""
    full_transcript: list = field(default_factory=list)
    prev_tail_wav: str | None = None


_sessions: dict[str, SessionState] = {}


def create_session() -> SessionState:
    session_id = str(uuid.uuid4())
    tmp_dir = os.path.join(config.SESSION_TMP_DIR, session_id)
    os.makedirs(tmp_dir, exist_ok=True)
    state = SessionState(session_id=session_id, tmp_dir=tmp_dir)
    _sessions[session_id] = state
    return state


def get_session(session_id: str) -> SessionState | None:
    return _sessions.get(session_id)


def end_session(session_id: str) -> SessionState | None:
    state = _sessions.pop(session_id, None)
    if state is not None:
        shutil.rmtree(state.tmp_dir, ignore_errors=True)
    return state


def record_chunk_text(state: SessionState, text: str) -> None:
    if not text:
        return
    state.full_transcript.append(text)
    words = state.tail_words.split() if state.tail_words else []
    words.extend(text.split())
    state.tail_words = " ".join(words[-10:])
