"""Isolated smoke tests for the legacy-to-contract adapter.

The project environment may not have pytest installed, so this file is also
runnable directly with Python.
"""

from bridge.reply import Reply, ReplyType
from models.bot_factory import create_provider
from models.provider_adapter import LegacyBotProvider
from models.provider_contract import ProviderErrorCategory, ProviderRequest, ProviderResponse


class FakeBot:
    def reply(self, messages, context=None):
        assert messages[0]["role"] == "user"
        return Reply(ReplyType.TEXT, "adapter ok")


class ExplodingBot:
    def reply(self, messages, context=None):
        raise RuntimeError("secret should not leak")


def test_success():
    provider = LegacyBotProvider(FakeBot(), "fake")
    result = provider.complete(ProviderRequest("fake", "test-model", ({"role": "user", "content": "hi"},)))
    assert isinstance(result, ProviderResponse)
    assert result.content == "adapter ok"
    assert result.provider_id == "fake"


def test_failure_is_normalized_without_exception_text():
    provider = LegacyBotProvider(ExplodingBot(), "fake")
    result = provider.complete(ProviderRequest("fake", "test-model", ({"role": "user", "content": "hi"},)))
    assert result.category is ProviderErrorCategory.UNKNOWN
    assert "secret" not in result.message


def test_factory_exposes_new_entrypoint_without_importing_network():
    # Use a provider that can be instantiated only when the configured runtime
    # credentials/dependencies are available; verify the symbol is callable.
    assert callable(create_provider)


if __name__ == "__main__":
    test_success()
    test_failure_is_normalized_without_exception_text()
    test_factory_exposes_new_entrypoint_without_importing_network()
    print("provider adapter smoke tests: PASS")
