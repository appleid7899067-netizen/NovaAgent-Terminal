"""Regression tests for MCP tool call failure status propagation."""

import pytest

from agent.tools.mcp.mcp_client import McpClient
from agent.tools.mcp.mcp_tool import McpTool


def _tool_with_response(monkeypatch, response):
    client = McpClient.__new__(McpClient)
    client.name = "test-server"
    monkeypatch.setattr(client, "_send_request", lambda *_args, **_kwargs: response)
    return client


def _tool_with_transport_error(monkeypatch, error):
    client = McpClient.__new__(McpClient)
    client.name = "test-server"

    def fail(*_args, **_kwargs):
        raise error

    monkeypatch.setattr(client, "_send_request", fail)
    return client


@pytest.mark.parametrize(
    "response",
    [
        {"error": {"code": -32603, "message": "remote failure"}},
        {"result": {"isError": True, "content": [{"type": "text", "text": "tool failed"}]}},
    ],
)
def test_server_reported_errors_become_failed_tool_results(monkeypatch, response):
    client = _tool_with_response(monkeypatch, response)
    tool = McpTool(client, {"name": "sample"}, "test-server")

    result = tool.execute({})

    assert result.status == "error"
    assert "failed" in str(result.result).lower()


def test_transport_errors_fail_without_echoing_exception_text(monkeypatch):
    client = _tool_with_transport_error(
        monkeypatch, RuntimeError("Authorization: bearer-secret-value")
    )
    tool = McpTool(client, {"name": "sample"}, "test-server")

    result = tool.execute({})

    assert result.status == "error"
    assert "bearer-secret-value" not in str(result.result)
    assert "RuntimeError" in str(result.result)


def test_valid_mcp_result_remains_successful(monkeypatch):
    client = _tool_with_response(
        monkeypatch,
        {"result": {"content": [{"type": "text", "text": "expected output"}]}},
    )
    tool = McpTool(client, {"name": "sample"}, "test-server")

    result = tool.execute({})

    assert result.status == "success"
    assert result.result == "expected output"
