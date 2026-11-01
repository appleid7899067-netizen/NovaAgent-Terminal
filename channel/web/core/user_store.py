"""Per-user accounts for the web console.

Model A: the console has one *root* password (``web_password`` in config.json)
and any number of named users created by root. Each user carries its own
password, so leaking one account does not open the others -- which is the whole
point of moving off the single shared password.

Storage lives in ``config.json`` under ``web_users``::

    "web_users": {
        "nut": {
            "salt": "<hex>",
            "hash": "<hex>",     # scrypt(password, salt)
            "n": 16384, "r": 8, "p": 1,
            "created": 1730000000
        }
    }

Passwords are never stored in clear. ``web_password`` stays the root credential
and is *not* hashed here: it is read from config at call time so the existing
console keeps working, and root always remains able to sign in even if the user
store is empty or corrupt.

The token that auth.py issues is signed per-identity, so a user's token cannot
be forged from another user's password and rotating one password does not
invalidate everyone else's sessions.
"""

import hashlib
import hmac
import json
import os
import re
import time
from typing import Dict, List, Optional

from common.log import logger
from config import conf

# scrypt parameters. n=2**14 keeps a login ~50ms on modest hardware -- slow
# enough to make offline brute force expensive, fast enough for an interactive
# console. Stored per-record so the cost can be raised later without breaking
# existing users.
_SCRYPT_N = 16384
_SCRYPT_R = 8
_SCRYPT_P = 1
_SALT_BYTES = 16
_HASH_BYTES = 32

_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,32}$")


class UserStoreError(Exception):
    """Raised for a caller-visible problem (bad name, duplicate, missing)."""


def _users() -> Dict[str, dict]:
    """Return the raw ``web_users`` mapping, tolerating a broken value."""
    raw = conf().get("web_users", {})
    if not isinstance(raw, dict):
        return {}
    return raw


def list_users() -> List[str]:
    """Sorted list of user names. Never includes root."""
    return sorted(_users().keys())


def user_exists(username: str) -> bool:
    return username in _users()


def is_valid_username(username: str) -> bool:
    return bool(username) and bool(_USERNAME_RE.match(username or ""))


def _hash_password(password: str, salt: bytes, n: int, r: int, p: int) -> str:
    dk = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=n,
        r=r,
        p=p,
        dklen=_HASH_BYTES,
        maxmem=64 * 1024 * 1024,
    )
    return dk.hex()


def create_user(username: str, password: str) -> None:
    """Add a user. Raises :class:`UserStoreError` on a bad name or duplicate."""
    username = (username or "").strip()
    if not is_valid_username(username):
        raise UserStoreError(
            "username must be 1-32 chars of A-Z a-z 0-9 _ . -"
        )
    if username == "root":
        raise UserStoreError("'root' is reserved")
    if not password or len(password) < 4:
        raise UserStoreError("password must be at least 4 characters")
    if user_exists(username):
        raise UserStoreError(f"user '{username}' already exists")

    salt = os.urandom(_SALT_BYTES)
    record = {
        "salt": salt.hex(),
        "hash": _hash_password(password, salt, _SCRYPT_N, _SCRYPT_R, _SCRYPT_P),
        "n": _SCRYPT_N,
        "r": _SCRYPT_R,
        "p": _SCRYPT_P,
        "created": int(time.time()),
    }
    _write_user(username, record)
    logger.info("[WebChannel] created web user '%s'", username)


def _write_user(username: str, record: dict) -> None:
    """Persist ``record`` under ``web_users[username]`` in config.json."""
    from channel.web.core._common import (
        _read_config_file_for_write,
        _write_config_file_for_write,
    )
    from config import get_data_root

    config_path = os.path.join(get_data_root(), "config.json")
    data = _read_config_file_for_write()
    users = data.get("web_users")
    if not isinstance(users, dict):
        users = {}
    users[username] = record
    data["web_users"] = users
    _write_config_file_for_write(config_path, data)


def delete_user(username: str) -> None:
    username = (username or "").strip()
    if not user_exists(username):
        raise UserStoreError(f"user '{username}' does not exist")
    from channel.web.core._common import (
        _read_config_file_for_write,
        _write_config_file_for_write,
    )
    from config import get_data_root

    config_path = os.path.join(get_data_root(), "config.json")
    data = _read_config_file_for_write()
    users = data.get("web_users")
    if isinstance(users, dict):
        users.pop(username, None)
        data["web_users"] = users
        _write_config_file_for_write(config_path, data)
    logger.info("[WebChannel] deleted web user '%s'", username)


def set_password(username: str, password: str) -> None:
    """Reset a user's password. Raises if the user or password is invalid."""
    username = (username or "").strip()
    if not user_exists(username):
        raise UserStoreError(f"user '{username}' does not exist")
    if not password or len(password) < 4:
        raise UserStoreError("password must be at least 4 characters")
    salt = os.urandom(_SALT_BYTES)
    record = {
        "salt": salt.hex(),
        "hash": _hash_password(password, salt, _SCRYPT_N, _SCRYPT_R, _SCRYPT_P),
        "n": _SCRYPT_N,
        "r": _SCRYPT_R,
        "p": _SCRYPT_P,
        "created": int(time.time()),
    }
    _write_user(username, record)
    logger.info("[WebChannel] rotated password for web user '%s'", username)


def verify_password(username: str, password: str) -> bool:
    """Constant-time check of a user password. False for unknown users."""
    record = _users().get((username or "").strip())
    if not isinstance(record, dict):
        return False
    try:
        salt = bytes.fromhex(record.get("salt", ""))
        expected = record.get("hash", "")
        n = int(record.get("n", _SCRYPT_N))
        r = int(record.get("r", _SCRYPT_R))
        p = int(record.get("p", _SCRYPT_P))
    except (TypeError, ValueError):
        logger.warning("[WebChannel] malformed web user record for '%s'", username)
        return False
    if not salt or not expected:
        return False
    try:
        actual = _hash_password(password or "", salt, n, r, p)
    except (ValueError, MemoryError) as e:
        logger.warning("[WebChannel] scrypt failed for '%s': %s", username, e)
        return False
    return hmac.compare_digest(actual, expected)


def public_list() -> List[dict]:
    """User summaries safe to send to the console (no hashes, no salts)."""
    out = []
    for name, record in sorted(_users().items()):
        created = None
        if isinstance(record, dict):
            created = record.get("created")
        out.append({"username": name, "created": created})
    return out
