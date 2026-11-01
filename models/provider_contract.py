"""Stable contract for chat model providers.

This module intentionally contains no provider-specific imports or network code.
Adapters can implement :class:`ModelProvider` without making the bridge depend on
an individual vendor SDK or response shape.
"""

from dataclasses import dataclass, field
from enum import Enum
from time import monotonic
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple


class ProviderErrorCategory(str, Enum):
    """Small, provider-neutral set of failures understood by the router."""

    AUTHENTICATION = "authentication"
    INVALID_REQUEST = "invalid_request"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    UNAVAILABLE = "unavailable"
    SAFETY = "safety"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class ProviderRequest:
    """Normalized request passed from the core to a model adapter.

    ``messages`` are copied to an immutable tuple at construction time so an
    adapter cannot mutate the caller's conversation accidentally. Values remain
    mappings to preserve compatibility with existing chat message dictionaries.
    """

    provider_id: str
    model: str
    messages: Tuple[Mapping[str, Any], ...]
    timeout_s: float = 60.0
    stream: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.provider_id.strip():
            raise ValueError("provider_id must not be empty")
        if not self.model.strip():
            raise ValueError("model must not be empty")
        if self.timeout_s <= 0:
            raise ValueError("timeout_s must be greater than zero")
        normalized_messages = tuple(self.messages)
        for message in normalized_messages:
            if not isinstance(message, Mapping):
                raise TypeError("messages must contain mapping objects")
            if not message.get("role"):
                raise ValueError("each message must include a role")
        object.__setattr__(self, "messages", normalized_messages)
        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True)
class ProviderUsage:
    """Usage information normalized across providers; all fields are optional."""

    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    estimated_cost: Optional[float] = None


@dataclass(frozen=True)
class ProviderResponse:
    """Normalized successful response returned by an adapter."""

    provider_id: str
    model: str
    content: str
    latency_ms: float
    usage: ProviderUsage = field(default_factory=ProviderUsage)
    finish_reason: Optional[str] = None
    request_id: Optional[str] = None

    def __post_init__(self) -> None:
        if self.latency_ms < 0:
            raise ValueError("latency_ms cannot be negative")


@dataclass(frozen=True)
class ProviderFailure:
    """Safe failure value; never store prompts, responses, or credentials here."""

    provider_id: str
    category: ProviderErrorCategory
    message: str
    retryable: bool = False
    request_id: Optional[str] = None


class ModelProvider:
    """Interface implemented by provider adapters."""

    provider_id = ""

    def complete(self, request: ProviderRequest):
        """Return ``ProviderResponse`` or ``ProviderFailure`` for one request."""
        raise NotImplementedError

    def capabilities(self) -> Mapping[str, bool]:
        """Return capability flags used by routing, without exposing secrets."""
        return {"chat": True, "stream": False, "vision": False, "tools": False}


def measure_latency(start: float) -> float:
    """Convert a monotonic start timestamp into milliseconds."""
    return round(max(0.0, monotonic() - start) * 1000, 3)
