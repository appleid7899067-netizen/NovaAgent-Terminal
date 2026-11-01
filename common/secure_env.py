"""Shared, defensive config-to-environment migration helpers."""

import os
import re
import stat
import tempfile
from typing import Callable, Dict

_ENV_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _read_env(path: str) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not os.path.lexists(path):
        return values
    if os.path.islink(path) or not os.path.isfile(path):
        raise OSError(f"refusing non-regular env file: {path}")
    with open(path, "r", encoding="utf-8") as stream:
        for raw in stream:
            line = raw.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                if _ENV_KEY.fullmatch(key):
                    values[key] = value.strip()
    return values


def sync_config_to_env(config_getter: Callable[[], dict], env_file: str, key_mapping: dict) -> bool:
    """Synchronize configured values without logging or exposing their contents."""
    env_dir = os.path.dirname(env_file)
    os.makedirs(env_dir, mode=0o700, exist_ok=True)
    try:
        os.chmod(env_dir, 0o700)
    except OSError:
        pass

    values = _read_env(env_file)
    config = config_getter()
    changed = False
    for config_key, env_key in key_mapping.items():
        raw = config.get(config_key, "")
        value = str(raw).strip() if raw else ""
        if value:
            if values.get(env_key) != value:
                values[env_key] = value
                changed = True
            os.environ[env_key] = value
        elif env_key in values:
            values.pop(env_key, None)
            os.environ.pop(env_key, None)
            changed = True

    if not changed:
        if os.path.lexists(env_file):
            if os.path.islink(env_file) or not os.path.isfile(env_file):
                raise OSError(f"refusing non-regular env file: {env_file}")
            os.chmod(env_file, 0o600)
        return False

    if os.path.lexists(env_file) and (os.path.islink(env_file) or not os.path.isfile(env_file)):
        raise OSError(f"refusing non-regular env file: {env_file}")
    if os.path.isfile(env_file):
        os.chmod(env_file, 0o600)
    lines = [
        "# Environment variables for agent",
        "# Auto-managed - synced from config.json on startup",
        "",
    ]
    lines.extend(f"{key}={value}" for key, value in sorted(values.items()))
    _write_secret_file_atomic(env_file, "\n".join(lines) + "\n")
    os.chmod(env_file, 0o600)
    return True


def _write_secret_file_atomic(path: str, content: str) -> None:
    """Replace a secret file atomically; never fall back to truncating in place."""
    directory = os.path.dirname(path)
    fd, temporary = tempfile.mkstemp(prefix=".env.", suffix=".tmp", dir=directory, text=True)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            fd = -1
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = ""
    finally:
        if fd != -1:
            os.close(fd)
        if temporary:
            try:
                os.unlink(temporary)
            except OSError:
                pass
