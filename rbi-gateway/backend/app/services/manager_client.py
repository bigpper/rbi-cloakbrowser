from __future__ import annotations

from urllib.parse import urljoin

import httpx


class ManagerClient:
    """Thin internal client for the official CloakBrowser-Manager API."""

    def __init__(
        self,
        base_url: str,
        auth_token: str | None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self._client = client

    def get_cdp_endpoint(self, manager_profile_id: str) -> str:
        return f"{self.base_url}/api/profiles/{manager_profile_id}/cdp"

    async def create_profile(self, payload: dict) -> dict:
        return await self._request("POST", "/api/profiles", json=payload)

    async def update_profile(self, manager_profile_id: str, payload: dict) -> dict:
        return await self._request("PUT", f"/api/profiles/{manager_profile_id}", json=payload)

    async def launch_profile(self, manager_profile_id: str) -> dict:
        return await self._request("POST", f"/api/profiles/{manager_profile_id}/launch")

    async def stop_profile(self, manager_profile_id: str) -> None:
        await self._request("POST", f"/api/profiles/{manager_profile_id}/stop")

    async def get_profile_status(self, manager_profile_id: str) -> dict:
        return await self._request("GET", f"/api/profiles/{manager_profile_id}/status")

    async def _request(self, method: str, path: str, **kwargs) -> dict:
        headers = kwargs.pop("headers", {})
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"

        if self._client:
            response = await self._client.request(method, path, headers=headers, **kwargs)
        else:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=30) as client:
                response = await client.request(method, path, headers=headers, **kwargs)

        response.raise_for_status()
        if not response.content:
            return {}
        return response.json()
