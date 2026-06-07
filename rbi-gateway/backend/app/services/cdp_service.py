from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any


ConnectOverCdp = Callable[[str], Awaitable[Any]]


class CdpService:
    """Backend-only CDP automation through Manager's internal CDP proxy."""

    SINGLE_PAGE_SCRIPT = """
        (() => {
            const forceSelf = () => {
                document.querySelectorAll('a[target="_blank"]').forEach((link) => {
                    link.setAttribute('target', '_self');
                });
            };
            window.open = (url) => {
                if (url) window.location.href = url;
                return window;
            };
            document.addEventListener('click', (event) => {
                const link = event.target && event.target.closest ? event.target.closest('a[target="_blank"]') : null;
                if (!link) return;
                event.preventDefault();
                window.location.href = link.href;
            }, true);
            forceSelf();
            new MutationObserver(forceSelf).observe(document.documentElement, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ['target'],
            });
        })();
    """

    def __init__(
        self,
        connect_over_cdp: ConnectOverCdp | None = None,
        cdp_headers: dict[str, str] | None = None,
    ) -> None:
        self._connect_over_cdp = connect_over_cdp
        self._cdp_headers = cdp_headers

    async def open_url(self, session, target_url: str) -> None:
        page = await self._page(session)
        await page.goto(target_url, wait_until="domcontentloaded")

    async def prepare_single_page_session(self, session) -> None:
        context, page = await self._context_and_page(session)
        await context.add_init_script(self.SINGLE_PAGE_SCRIPT)
        for extra_page in list(context.pages[1:]):
            try:
                extra_url = getattr(extra_page, "url", None)
                await extra_page.close()
                if extra_url and extra_url != "about:blank":
                    await page.goto(extra_url, wait_until="domcontentloaded")
            except Exception:
                continue
        await page.evaluate(self.SINGLE_PAGE_SCRIPT)

    async def insert_text(self, session, text: str) -> None:
        page = await self._page(session)
        await page.keyboard.insert_text(text)

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
        _, page = await self._context_and_page(session)
        return page

    async def _context_and_page(self, session):
        if not session.cdp_endpoint_internal:
            raise RuntimeError("Session does not have an internal CDP endpoint")
        browser = await self._connect(session.cdp_endpoint_internal)
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        if context.pages:
            return context, context.pages[0]
        return context, await context.new_page()

    async def _connect(self, endpoint: str):
        if self._connect_over_cdp:
            return await self._connect_over_cdp(endpoint)

        from playwright.async_api import async_playwright

        playwright = await async_playwright().start()
        return await playwright.chromium.connect_over_cdp(endpoint, headers=self._cdp_headers)
