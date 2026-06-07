import pytest

from app.services.url_policy_service import UrlPolicyError, validate_target_url


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "chrome://settings",
        "devtools://devtools/bundled/inspector.html",
        "about:blank",
        "javascript:alert(1)",
        "data:text/plain,hello",
        "ftp://example.com/file",
    ],
)
def test_validate_target_url_rejects_unsafe_schemes(url: str) -> None:
    with pytest.raises(UrlPolicyError):
        validate_target_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost",
        "http://127.0.0.1",
        "http://10.0.0.1",
        "http://172.16.0.1",
        "http://192.168.1.1",
        "http://169.254.169.254/latest/meta-data",
        "http://[::1]/",
        "http://[fc00::1]/",
        "http://[fe80::1]/",
    ],
)
def test_validate_target_url_rejects_private_and_metadata_hosts(url: str) -> None:
    with pytest.raises(UrlPolicyError):
        validate_target_url(url)


def test_validate_target_url_allows_public_https_url() -> None:
    normalized = validate_target_url("https://example.com/path?q=secret")

    assert normalized == "https://example.com/path?q=secret"


def test_validate_target_url_requires_hostname() -> None:
    with pytest.raises(UrlPolicyError):
        validate_target_url("https:///missing-host")
