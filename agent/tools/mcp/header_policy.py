"""Validation policy for user-supplied MCP HTTP headers."""

import re
from typing import Mapping, Dict

_RESERVED = {
    "authorization", "cookie", "host", "content-length", "transfer-encoding",
    "connection", "proxy-authorization", "proxy-connection", "upgrade",
}
_TOKEN = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
_MAX_NAME = 128
_MAX_VALUE = 4096


def validate_custom_headers(headers: Mapping) -> Dict[str, str]:
    if not isinstance(headers, Mapping):
        raise ValueError("custom headers must be an object")
    result: Dict[str, str] = {}
    for raw_name, raw_value in headers.items():
        name, value = str(raw_name), str(raw_value)
        if len(name) > _MAX_NAME or not _TOKEN.fullmatch(name):
            raise ValueError("invalid custom header name")
        if name.lower() in _RESERVED:
            raise ValueError(f"reserved custom header is not allowed: {name}")
        if len(value) > _MAX_VALUE or "\r" in value or "\n" in value or any(ord(c) < 32 for c in value):
            raise ValueError(f"invalid custom header value: {name}")
        result[name] = value
    return result
