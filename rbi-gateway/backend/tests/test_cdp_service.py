import pytest

from app.services.cdp_service import CdpService
from app.services.session_service import StoredSession


class FakePage:
    def __init__(self) -> None:
        self.actions: list[tuple[str, str | None]] = []

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


class FakeContext:
    def __init__(self, page: FakePage) -> None:
        self.pages = [page]

    async def new_page(self) -> FakePage:
        page = FakePage()
        self.pages.append(page)
        return page


class FakeBrowser:
    def __init__(self, page: FakePage) -> None:
        self.contexts = [FakeContext(page)]


def fake_session() -> StoredSession:
    return StoredSession(
        id="session-1",
        user_id="user-1",
        profile_id="profile-1",
        manager_profile_id="manager-profile-1",
        target_url_encrypted="enc",
        viewer_token_hash="hash",
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
