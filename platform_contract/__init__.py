"""Platform Contract v1 primitives for NovaAgent.

This package is intentionally independent from Web/UI and provider adapters.
It defines the stable execution vocabulary that future API and worker layers
can consume without importing each other's implementation details.
"""

from .models import (
    CONTRACT_VERSION,
    AgentRef,
    Run,
    RunEvent,
    RunState,
    SessionRef,
)
from .run_service import (
    IdempotencyConflict,
    InMemoryRunStore,
    InvalidRunTransition,
    RunNotFound,
    RunService,
)

__all__ = [
    "CONTRACT_VERSION",
    "AgentRef",
    "Run",
    "RunEvent",
    "RunState",
    "SessionRef",
    "IdempotencyConflict",
    "InMemoryRunStore",
    "InvalidRunTransition",
    "RunNotFound",
    "RunService",
]
