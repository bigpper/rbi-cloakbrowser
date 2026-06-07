from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any


ConnectOverCdp = Callable[[str], Awaitable[Any]]


class CdpService:
    """Backend-only CDP automation through Manager's internal CDP proxy."""

    def __init__(self, connect_over_cdp: ConnectOverCdp | None = None) -> None:
        self._connect_over_cdp = connect_over_cdp

    async def open_url(self, session, target_url: str) -> None:
        page = await self._page(session)
        await page.goto(target_url, wait_until="domcontentloaded")

    async def reload(self, session) -> None:
        page = await self._page(session)
        await page.reload(wait_until="domcontentloaded")

    async def go_back(self, session) -> None:
        page = await self._page(session)
        await page.go_back(wait_until="domcontentloaded")

    async def go_forward(self, session) -> None:
        page = await self._page(session)
        await page.go_forward(wait_until="domcontentloaded")

    async def get_page_title(self, session) -> str:
        page = await self._page(session)
        return await page.title()

    async def _page(self, session):
        if not session.cdp_endpoint_internal:
            raise RuntimeError("Session does not have an internal CDP endpoint")
        browser = await self._connect(session.cdp_endpoint_internal)
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        if context.pages:
            return context.pages[0]
        return await context.new_page()

    async def _connect(self, endpoint: str):
        if self._connect_over_cdp:
            return await self._connect_over_cdp(endpoint)

        from playwright.async_api import async_playwright

        playwright = await async_playwright().start()
        return await playwright.chromium.connect_over_cdp(endpoint)
