"""Transport-neutral entities for Platform Contract v1."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping, Optional
from uuid import uuid4

CONTRACT_VERSION = "1.0"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RunState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELLED = "cancelled"


TERMINAL_STATES = frozenset({RunState.SUCCEEDED, RunState.FAILED, RunState.CANCELLED})
_ALLOWED_TRANSITIONS = {
    RunState.QUEUED: frozenset({RunState.RUNNING, RunState.CANCEL_REQUESTED, RunState.CANCELLED}),
    RunState.RUNNING: frozenset({RunState.SUCCEEDED, RunState.FAILED, RunState.CANCEL_REQUESTED}),
    RunState.CANCEL_REQUESTED: frozenset({RunState.CANCELLED, RunState.FAILED}),
    RunState.SUCCEEDED: frozenset(),
    RunState.FAILED: frozenset(),
    RunState.CANCELLED: frozenset(),
}


@dataclass(frozen=True)
class AgentRef:
    id: str


@dataclass(frozen=True)
class SessionRef:
    id: str


@dataclass
class Run:
    agent: AgentRef
    session: SessionRef
    input: str
    id: str = field(default_factory=lambda: str(uuid4()))
    state: RunState = RunState.QUEUED
    idempotency_key: Optional[str] = None
    output: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def transition(self, target: RunState, *, output: Optional[str] = None, error: Optional[str] = None) -> None:
        if target not in _ALLOWED_TRANSITIONS[self.state]:
            raise ValueError(f"invalid run transition: {self.state.value} -> {target.value}")
        if target == RunState.SUCCEEDED and not output:
            raise ValueError("succeeded run requires output")
        if target == RunState.FAILED and not error:
            raise ValueError("failed run requires error")
        if target in (RunState.CANCELLED, RunState.CANCEL_REQUESTED) and output:
            raise ValueError("cancelled run cannot carry output")
        self.state = target
        self.output = output
        self.error = error
        self.updated_at = utc_now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": CONTRACT_VERSION,
            "id": self.id,
            "agent_id": self.agent.id,
            "session_id": self.session.id,
            "input": self.input,
            "state": self.state.value,
            "idempotency_key": self.idempotency_key,
            "output": self.output,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass(frozen=True)
class RunEvent:
    run_id: str
    sequence: int
    type: str
    data: Mapping[str, Any]
    created_at: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "contract_version": CONTRACT_VERSION,
            "run_id": self.run_id,
            "sequence": self.sequence,
            "type": self.type,
            "data": dict(self.data),
            "created_at": self.created_at.isoformat(),
        }
