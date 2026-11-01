from __future__ import annotations

import pytest

from platform_contract import (
    InvalidRunTransition,
    RunService,
    RunState,
)


def test_create_run_emits_first_event() -> None:
    service = RunService()

    run = service.create_run("agent-a", "session-1", "hello")

    assert run.state is RunState.QUEUED
    events = service.store.events(run.id)
    assert len(events) == 1
    assert events[0].sequence == 1
    assert events[0].type == "run.created"


def test_happy_path_preserves_event_order() -> None:
    service = RunService()
    run = service.create_run("agent-a", "session-1", "hello")

    service.transition(run.id, RunState.RUNNING)
    service.transition(run.id, RunState.SUCCEEDED, output="world")

    assert run.state is RunState.SUCCEEDED
    assert run.output == "world"
    assert [event.sequence for event in service.store.events(run.id)] == [1, 2, 3]
    assert [event.type for event in service.store.events(run.id)] == [
        "run.created",
        "run.running",
        "run.succeeded",
    ]


def test_invalid_transition_is_exposed_as_domain_error() -> None:
    service = RunService()
    run = service.create_run("agent-a", "session-1", "hello")

    with pytest.raises(InvalidRunTransition):
        service.transition(run.id, RunState.SUCCEEDED, output="too soon")


def test_idempotency_returns_same_run() -> None:
    service = RunService()

    first = service.create_run("agent-a", "session-1", "hello", idempotency_key="request-1")
    second = service.create_run("agent-a", "session-1", "hello", idempotency_key="request-1")

    assert second.id == first.id
    assert len(service.store.events(first.id)) == 1


def test_cancel_queued_run_is_terminal() -> None:
    service = RunService()
    run = service.create_run("agent-a", "session-1", "hello")

    service.cancel(run.id)

    assert run.state is RunState.CANCELLED
    assert service.cancel(run.id).state is RunState.CANCELLED


def test_cancel_running_run_requires_follow_up_cancellation() -> None:
    service = RunService()
    run = service.create_run("agent-a", "session-1", "hello")
    service.transition(run.id, RunState.RUNNING)

    service.cancel(run.id)
    assert run.state is RunState.CANCEL_REQUESTED

    service.transition(run.id, RunState.CANCELLED)
    assert run.state is RunState.CANCELLED


@pytest.mark.parametrize(
    "agent_id,session_id,input_text",
    [("", "session-1", "hello"), ("agent-a", "", "hello"), ("agent-a", "session-1", "")],
)
def test_create_run_rejects_missing_required_input(agent_id: str, session_id: str, input_text: str) -> None:
    with pytest.raises(ValueError):
        RunService().create_run(agent_id, session_id, input_text)
