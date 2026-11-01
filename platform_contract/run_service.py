"""Application service for the first executable Run contract.

The store is deliberately in-memory for v1: this proves semantics without
pretending that process memory is durable persistence. A repository boundary
keeps the later SQLite/queue implementation swappable.
"""

from __future__ import annotations

from threading import RLock
from typing import Optional

from .models import AgentRef, Run, RunEvent, RunState, SessionRef


class RunNotFound(KeyError):
    pass


class IdempotencyConflict(ValueError):
    pass


class InvalidRunTransition(ValueError):
    pass


class InMemoryRunStore:
    def __init__(self) -> None:
        self._runs: dict[str, Run] = {}
        self._events: dict[str, list[RunEvent]] = {}
        self._idempotency: dict[tuple[str, str], str] = {}
        self._lock = RLock()

    def create(self, run: Run) -> Run:
        with self._lock:
            if run.idempotency_key:
                key = (run.agent.id, run.idempotency_key)
                existing = self._idempotency.get(key)
                if existing and existing != run.id:
                    raise IdempotencyConflict("idempotency key already belongs to another run")
                self._idempotency[key] = run.id
            self._runs[run.id] = run
            self._events[run.id] = []
            return run

    def get(self, run_id: str) -> Run:
        with self._lock:
            try:
                return self._runs[run_id]
            except KeyError:
                raise RunNotFound(run_id) from None

    def find_idempotent(self, agent_id: str, key: str) -> Optional[Run]:
        with self._lock:
            run_id = self._idempotency.get((agent_id, key))
            return self._runs.get(run_id) if run_id else None

    def append_event(self, event: RunEvent) -> RunEvent:
        with self._lock:
            if event.run_id not in self._runs:
                raise RunNotFound(event.run_id)
            expected = len(self._events[event.run_id]) + 1
            if event.sequence != expected:
                raise ValueError(f"event sequence must be {expected}")
            self._events[event.run_id].append(event)
            return event

    def events(self, run_id: str) -> list[RunEvent]:
        with self._lock:
            if run_id not in self._runs:
                raise RunNotFound(run_id)
            return list(self._events[run_id])


class RunService:
    def __init__(self, store: InMemoryRunStore | None = None) -> None:
        self.store = store or InMemoryRunStore()

    def create_run(self, agent_id: str, session_id: str, input_text: str, *, idempotency_key: str | None = None) -> Run:
        if not agent_id.strip() or not session_id.strip():
            raise ValueError("agent_id and session_id are required")
        if not input_text.strip():
            raise ValueError("input must not be empty")
        if idempotency_key:
            existing = self.store.find_idempotent(agent_id, idempotency_key)
            if existing:
                return existing
        run = Run(agent=AgentRef(agent_id), session=SessionRef(session_id), input=input_text, idempotency_key=idempotency_key)
        self.store.create(run)
        self._emit(run, "run.created")
        return run

    def transition(self, run_id: str, target: RunState, *, output: str | None = None, error: str | None = None) -> Run:
        run = self.store.get(run_id)
        try:
            run.transition(target, output=output, error=error)
        except ValueError as exc:
            raise InvalidRunTransition(str(exc)) from exc
        self._emit(run, f"run.{target.value}", {"output": output, "error": error})
        return run

    def cancel(self, run_id: str) -> Run:
        run = self.store.get(run_id)
        if run.state == RunState.QUEUED:
            return self.transition(run_id, RunState.CANCELLED)
        if run.state == RunState.RUNNING:
            return self.transition(run_id, RunState.CANCEL_REQUESTED)
        return run

    def _emit(self, run: Run, event_type: str, data: dict | None = None) -> None:
        self.store.append_event(RunEvent(run_id=run.id, sequence=len(self.store.events(run.id)) + 1, type=event_type, data=data or {}))
