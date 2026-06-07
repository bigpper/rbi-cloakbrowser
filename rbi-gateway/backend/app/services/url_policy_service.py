from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse, urlunparse


class UrlPolicyError(ValueError):
    """Raised when a submitted target URL is not allowed for RBI navigation."""


_ALLOWED_SCHEMES = {"http", "https"}
_BLOCKED_HOSTNAMES = {"localhost", "localhost.localdomain"}
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def _is_blocked_ip(value: str) -> bool:
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False
    return any(ip in network for network in _BLOCKED_NETWORKS)


def _resolved_private_address(hostname: str) -> bool:
    try:
        results = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        # The remote browser will fail navigation if the name is truly
        # unresolved. Do not make unit tests or local development depend on DNS.
        return False

    for result in results:
        address = result[4][0]
        if _is_blocked_ip(address):
            return True
    return False


def validate_target_url(raw_url: str) -> str:
    """Validate and normalize a target URL before remote navigation."""
    parsed = urlparse(raw_url.strip())
    scheme = parsed.scheme.lower()
    if scheme not in _ALLOWED_SCHEMES:
        raise UrlPolicyError("URL scheme is not allowed")

    if not parsed.hostname:
        raise UrlPolicyError("URL hostname is required")

    hostname = parsed.hostname.lower().rstrip(".")
    if hostname in _BLOCKED_HOSTNAMES or hostname.endswith(".localhost"):
        raise UrlPolicyError("Localhost targets are not allowed")

    if _is_blocked_ip(hostname) or _resolved_private_address(hostname):
        raise UrlPolicyError("Private or metadata network targets are not allowed")

    normalized_netloc = parsed.netloc
    normalized = parsed._replace(scheme=scheme, netloc=normalized_netloc)
    return urlunparse(normalized)
