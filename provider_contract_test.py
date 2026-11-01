import pytest

from models.provider_contract import (
    ModelProvider,
    ProviderErrorCategory,
    ProviderFailure,
    ProviderRequest,
    ProviderResponse,
    measure_latency,
)


def test_request_normalizes_messages_and_rejects_invalid_timeout():
    request = ProviderRequest(
        provider_id="astra",
        model="reasoning-model",
        messages=({"role": "user", "content": "hello"},),
    )
    assert request.messages[0]["role"] == "user"

    with pytest.raises(ValueError, match="timeout_s"):
        ProviderRequest("astra", "model", (), timeout_s=0)


def test_request_rejects_messages_without_roles():
    with pytest.raises(ValueError, match="role"):
        ProviderRequest("astra", "model", ({"content": "missing role"},))


def test_response_and_failure_are_provider_neutral():
    response = ProviderResponse("astra", "model", "ok", 12.5)
    failure = ProviderFailure(
        "grok", ProviderErrorCategory.RATE_LIMIT, "try later", retryable=True
    )
    assert response.content == "ok"
    assert failure.retryable is True
    assert failure.category.value == "rate_limit"


def test_base_provider_exposes_safe_default_capabilities():
    provider = ModelProvider()
    assert provider.capabilities()["chat"] is True
    assert "api_key" not in provider.capabilities()


def test_measure_latency_is_non_negative():
    assert measure_latency(0) >= 0
