import httpx
import pytest

from app.services.manager_client import ManagerClient


@pytest.mark.asyncio
async def test_manager_client_uses_real_profile_api_paths() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/api/profiles" and request.method == "POST":
            return httpx.Response(201, json={"id": "manager-profile-1", "name": "Profile"})
        if request.url.path == "/api/profiles/manager-profile-1/launch":
            return httpx.Response(200, json={"status": "running", "cdp_url": "/api/profiles/manager-profile-1/cdp"})
        if request.url.path == "/api/profiles/manager-profile-1/status":
            return httpx.Response(200, json={"status": "running", "cdp_url": "/api/profiles/manager-profile-1/cdp"})
        if request.url.path == "/api/profiles/manager-profile-1/stop":
            return httpx.Response(200, json={"ok": True})
        return httpx.Response(404)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://manager:8080")
    manager = ManagerClient(base_url="http://manager:8080", auth_token="secret", client=client)

    profile = await manager.create_profile({"name": "Profile"})
    launch = await manager.launch_profile(profile["id"])
    status = await manager.get_profile_status(profile["id"])
    await manager.stop_profile(profile["id"])

    assert launch["cdp_url"] == "/api/profiles/manager-profile-1/cdp"
    assert status["status"] == "running"
    assert [request.url.path for request in requests] == [
        "/api/profiles",
        "/api/profiles/manager-profile-1/launch",
        "/api/profiles/manager-profile-1/status",
        "/api/profiles/manager-profile-1/stop",
    ]
    assert all(request.headers["authorization"] == "Bearer secret" for request in requests)


@pytest.mark.asyncio
async def test_manager_client_cdp_endpoint_is_internal_url() -> None:
    manager = ManagerClient(base_url="http://cloakbrowser-manager:8080", auth_token="secret")

    assert manager.get_cdp_endpoint("abc") == "http://cloakbrowser-manager:8080/api/profiles/abc/cdp"
