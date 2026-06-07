from app.services.privacy_log_service import domain_hash, mask_url_for_log


def test_mask_url_for_log_removes_path_and_query() -> None:
    masked = mask_url_for_log("https://example.com/account?token=secret")

    assert masked == "https://example.com/[redacted]"


def test_mask_url_for_log_handles_invalid_url_without_leaking_input() -> None:
    masked = mask_url_for_log("not a url with secret=value")

    assert masked == "[invalid-url]"


def test_domain_hash_is_stable_and_does_not_return_domain() -> None:
    first = domain_hash("https://example.com/path?token=secret")
    second = domain_hash("https://example.com/other")

    assert first == second
    assert "example.com" not in first
