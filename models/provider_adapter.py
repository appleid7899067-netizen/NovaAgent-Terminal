"""Adapters from the legacy Bot interface to the provider contract."""

from time import monotonic
from typing import Any, Mapping

from bridge.reply import Reply
from models.provider_contract import (
    ModelProvider,
    ProviderErrorCategory,
    ProviderFailure,
    ProviderRequest,
    ProviderResponse,
    measure_latency,
)


class LegacyBotProvider(ModelProvider):
    """Expose an existing ``Bot`` as a contract-compliant provider.

    This is deliberately an adapter, not a rewrite of provider implementations.
    The legacy bot remains responsible for credentials, transport, retries and
    provider-specific response parsing while the core receives one stable shape.
    """

    def __init__(self, bot: Any, provider_id: str):
        if bot is None:
            raise ValueError("bot must not be None")
        if not provider_id or not provider_id.strip():
            raise ValueError("provider_id must not be empty")
        self.bot = bot
        self.provider_id = provider_id

    def complete(self, request: ProviderRequest):
        if request.provider_id != self.provider_id:
            return ProviderFailure(
                provider_id=self.provider_id,
                category=ProviderErrorCategory.INVALID_REQUEST,
                message="request provider_id does not match adapter",
                retryable=False,
            )
        if request.stream:
            return ProviderFailure(
                provider_id=self.provider_id,
                category=ProviderErrorCategory.INVALID_REQUEST,
                message="legacy bot adapter does not normalize streaming yet",
                retryable=False,
            )

        started = monotonic()
        try:
            reply = self.bot.reply(list(request.messages), context=None)
            content = reply.content if isinstance(reply, Reply) else getattr(reply, "content", reply)
            if content is None:
                content = ""
            return ProviderResponse(
                provider_id=self.provider_id,
                model=request.model,
                content=str(content),
                latency_ms=measure_latency(started),
            )
        except TimeoutError:
            return ProviderFailure(
                provider_id=self.provider_id,
                category=ProviderErrorCategory.TIMEOUT,
                message="provider request timed out",
                retryable=True,
            )
        except Exception as exc:  # noqa: BLE001 - adapter must normalize legacy failures
            return ProviderFailure(
                provider_id=self.provider_id,
                category=ProviderErrorCategory.UNKNOWN,
                message=f"legacy provider failed: {type(exc).__name__}",
                retryable=False,
            )

    def capabilities(self) -> Mapping[str, bool]:
        return {"chat": True, "stream": False, "vision": False, "tools": False}
