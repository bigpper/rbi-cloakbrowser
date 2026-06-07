from __future__ import annotations

import hashlib
import os
from urllib.parse import urlparse


def _hostname(raw_url: str) -> str | None:
    parsed = urlparse(raw_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    return parsed.hostname.lower().rstrip(".")


def mask_url_for_log(raw_url: str) -> str:
    """Return a log-safe URL form without path, query, fragment, or credentials."""
    parsed = urlparse(raw_url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return "[invalid-url]"

    port = f":{parsed.port}" if parsed.port else ""
    return f"{parsed.scheme}://{parsed.hostname.lower()}{port}/[redacted]"


def domain_hash(raw_url: str) -> str:
    """Hash only the hostname so audit logs can group domains without storing URLs."""
    hostname = _hostname(raw_url)
    if not hostname:
        hostname = "[invalid-url]"
    salt = os.getenv("TOKEN_HASH_SECRET", "dev-domain-hash-salt")
    return hashlib.sha256(f"{salt}:{hostname}".encode("utf-8")).hexdigest()
