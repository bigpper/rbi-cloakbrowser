# RBI Gateway MVP

RBI Gateway wraps the official CloakBrowser and CloakBrowser-Manager projects into a remote browser gateway. The local browser connects only to the Gateway. Target sites are opened by remote CloakBrowser profiles running behind the Gateway.

## Upstream

Vendored official repositories:

- `vendor/CloakBrowser`
- `vendor/CloakBrowser-Manager`

The Gateway does not reimplement Chromium, fingerprinting, CDP, VNC, noVNC, profile persistence, or the browser launcher.

## Run

```bash
cp .env.example .env
docker compose up --build
```

Open `http://localhost`.

## Create A Session

1. Open the Home page.
2. Enter `https://example.com`.
3. Click `打开远程浏览器`.
4. The browser navigates to `/session/{viewer_token}`.
5. The remote CloakBrowser opens the target site through backend CDP automation.

The target URL is not placed in the local browser address bar.

## Profiles

Open `/profiles` to create and delete Gateway profiles. Each Gateway profile maps to a CloakBrowser-Manager profile. Manager stores profile browser data in the `cloakprofiles` Docker volume.

## Proxy

Profile API accepts proxy settings in the Gateway schema. Proxy credentials must be treated as secrets and should be encrypted before production use. Do not log proxy passwords.

## HTTPS

Local Compose generates a self-signed certificate for development. In production, mount real certificates for Nginx and keep `/viewer-ws/` on WSS.

See `docs/deployment.md`.

## Ports That Must Not Be Public

Do not expose:

- `cloakbrowser-manager:8080`
- CDP ports
- VNC ports
- PostgreSQL
- Redis
- Docker daemon

Only expose the Gateway Nginx service.

## Verify Isolation

Use browser developer tools on the local browser:

- Address bar should show `/session/{viewer_token}`.
- Network requests should go to the Gateway origin.
- Target navigation should call Gateway APIs, not direct target-site requests.

## Tests

Backend:

```bash
python -m pytest -c rbi-gateway/backend/pytest.ini rbi-gateway/backend/tests -q
```

Frontend:

```bash
npm --prefix rbi-gateway/frontend run build
```

## Current MVP Limits

- Authentication is a demo `X-User-Id` shim and must be replaced before production.
- PostgreSQL schema is present, while the current MVP service store is in-memory.
- Viewer token validation is implemented in the backend, but session metadata is not yet persisted across Gateway restarts.
- Full Docker runtime still requires local validation with CloakBrowser binary download and Manager startup.
