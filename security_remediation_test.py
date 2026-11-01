"""Dependency-free regression tests for the security remediation."""
import os
import stat
import tempfile

from common.secure_env import sync_config_to_env
from agent.tools.mcp.header_policy import validate_custom_headers


def test_secure_env_sync_and_mode():
    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, ".env")
        changed = sync_config_to_env(
            lambda: {"fake_key": "fake-secret", "fake_base": "https://example.test"},
            path,
            {"fake_key": "FAKE_KEY", "fake_base": "FAKE_BASE"},
        )
        assert changed is True
        assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
        content = open(path, encoding="utf-8").read()
        assert "FAKE_KEY=fake-secret" in content
        assert os.environ["FAKE_KEY"] == "fake-secret"


def test_secure_env_rejects_symlink():
    with tempfile.TemporaryDirectory() as directory:
        target = os.path.join(directory, "target")
        path = os.path.join(directory, ".env")
        open(target, "w", encoding="utf-8").close()
        os.symlink(target, path)
        try:
            sync_config_to_env(lambda: {"key": "value"}, path, {"key": "KEY"})
        except OSError:
            return
        raise AssertionError("symlink env file was accepted")


def test_header_policy():
    assert validate_custom_headers({"X-Trace": "safe"}) == {"X-Trace": "safe"}
    for headers in (
        {"Authorization": "Bearer fake"},
        {"Cookie": "secret=fake"},
        {"X-Trace": "line\nbreak"},
        {"Host": "evil.example"},
        {"X-Trace": "x" * 4097},
        {"X" * 129: "value"},
    ):
        try:
            validate_custom_headers(headers)
        except ValueError:
            continue
        raise AssertionError(f"unsafe header accepted: {headers.keys()}")


def test_secure_env_rejects_directory():
    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, ".env")
        os.mkdir(path)
        try:
            sync_config_to_env(lambda: {"key": "value"}, path, {"key": "KEY"})
        except OSError:
            return
        raise AssertionError("directory env path was accepted")


if __name__ == "__main__":
    for name, function in sorted(globals().items()):
        if name.startswith("test_"):
            function()
    print("security remediation tests: PASS")
