import pytest

from app.services.cdp_service import CdpService
from app.services.session_service import StoredSession


class FakePage:
    def __init__(self) -> None:
        self.actions: list[tuple[str, str | None]] = []
        self.closed = False
        self.evaluated_scripts: list[str] = []
        self.keyboard = self.FakeKeyboard(self)

    class FakeKeyboard:
        def __init__(self, page: "FakePage") -> None:
            self.page = page

        async def insert_text(self, text: str) -> None:
            self.page.actions.append(("insert_text", text))

    async def goto(self, url: str, wait_until: str = "domcontentloaded") -> None:
        self.actions.append(("goto", url))

    async def reload(self, wait_until: str = "domcontentloaded") -> None:
        self.actions.append(("reload", None))

    async def go_back(self, wait_until: str = "domcontentloaded") -> None:
        self.actions.append(("go_back", None))

    async def go_forward(self, wait_until: str = "domcontentloaded") -> None:
        self.actions.append(("go_forward", None))

    async def title(self) -> str:
        return "Remote Title"

    async def close(self) -> None:
        self.closed = True

    async def evaluate(self, script: str) -> None:
        self.evaluated_scripts.append(script)


class FakeContext:
    def __init__(self, page: FakePage, extra_pages: list[FakePage] | None = None) -> None:
        self.pages = [page, *(extra_pages or [])]
        self.init_scripts: list[str] = []

    async def new_page(self) -> FakePage:
        page = FakePage()
        self.pages.append(page)
        return page

    async def add_init_script(self, script: str) -> None:
        self.init_scripts.append(script)


class FakeBrowser:
    def __init__(self, page: FakePage, extra_pages: list[FakePage] | None = None) -> None:
        self.contexts = [FakeContext(page, extra_pages)]


def fake_session() -> StoredSession:
    return StoredSession(
        id="session-1",
        user_id="user-1",
        profile_id="profile-1",
        manager_profile_id="manager-profile-1",
        target_url_encrypted="enc",
        viewer_token_hash="hash",
        audio_token_hash="audio-hash",
        display_profile="high",
        status="running",
        cdp_endpoint_internal="http://manager/api/profiles/manager-profile-1/cdp",
        viewer_endpoint_internal="/api/profiles/manager-profile-1/vnc",
        expires_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
        last_active_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
        created_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
    )


@pytest.mark.asyncio
async def test_open_url_connects_over_internal_cdp_and_navigates_page() -> None:
    page = FakePage()
    connected: list[str] = []

    async def connector(endpoint: str):
        connected.append(endpoint)
        return FakeBrowser(page)

    service = CdpService(connect_over_cdp=connector)
    session = fake_session()

    await service.open_url(session, "https://example.com")

    assert connected == ["http://manager/api/profiles/manager-profile-1/cdp"]
    assert page.actions == [("goto", "https://example.com")]


@pytest.mark.asyncio
async def test_prepare_single_page_session_closes_extra_pages_and_blocks_new_windows() -> None:
    page = FakePage()
    extra = FakePage()

    async def connector(endpoint: str):
        return FakeBrowser(page, [extra])

    service = CdpService(connect_over_cdp=connector)

    await service.prepare_single_page_session(fake_session())

    context = (await connector("ignored")).contexts[0]
    assert extra.closed is True
    assert "window.open" in page.evaluated_scripts[0]
    assert "target" in page.evaluated_scripts[0]


@pytest.mark.asyncio
async def test_insert_text_uses_keyboard_insert_text() -> None:
    page = FakePage()

    async def connector(endpoint: str):
        return FakeBrowser(page)

    service = CdpService(connect_over_cdp=connector)

    await service.insert_text(fake_session(), "中文输入")

    assert page.actions == [("insert_text", "中文输入")]


@pytest.mark.asyncio
async def test_navigation_helpers_use_existing_remote_page() -> None:
    page = FakePage()

    async def connector(endpoint: str):
        return FakeBrowser(page)

    service = CdpService(connect_over_cdp=connector)
    session = fake_session()

    await service.reload(session)
    await service.go_back(session)
    await service.go_forward(session)
    title = await service.get_page_title(session)

    assert page.actions == [("reload", None), ("go_back", None), ("go_forward", None)]
    assert title == "Remote Title"
