# RBI Gateway Architecture

## Goal

This project wraps the official CloakBrowser and CloakBrowser-Manager projects into a product-ready RBI / Remote Browser Gateway.

The user's local browser must connect only to the Gateway domain. Target websites are opened by remote CloakBrowser instances running behind the Gateway. The local browser receives a remote browser viewer and sends input events through the authenticated Gateway path.

## Upstream Components

The official repositories are vendored under `vendor/`:

- `vendor/CloakBrowser`: stealth Chromium wrapper and binary download/runtime layer.
- `vendor/CloakBrowser-Manager`: FastAPI + React manager for browser profiles, KasmVNC/noVNC viewing, clipboard relay, and CDP proxying.

The Gateway must not duplicate or fork core browser behavior from either upstream project.

## CloakBrowser-Manager Capabilities To Reuse

The current Manager implementation already provides:

- Profile CRUD through `/api/profiles`.
- Persistent per-profile browser data under `/data/profiles/{profile_id}`.
- CloakBrowser launch through `launch_persistent_context_async()`.
- Per-profile proxy, timezone, locale, platform, screen size, fingerprint seed, launch args, and headless/humanize settings.
- KasmVNC lifecycle management with WebSocket-only VNC bound to `127.0.0.1`.
- noVNC React viewer via `@novnc/novnc`.
- VNC WebSocket proxy at `/api/profiles/{profile_id}/vnc`.
- CDP proxy at `/api/profiles/{profile_id}/cdp`.
- CDP discovery proxy at `/api/profiles/{profile_id}/cdp/json/version` and `/json/list`.
- Clipboard relay endpoints at `/api/profiles/{profile_id}/clipboard`.
- Optional `AUTH_TOKEN` protection for Manager API and WebSocket paths.

The Gateway will call these APIs over Docker internal networking. It will not copy Manager's browser startup, VNC proxy, CDP proxy, or fingerprint logic.

## Gateway Responsibilities

`rbi-gateway` adds the product and security layer around Manager:

- User authentication and per-user ownership.
- Gateway profile records that map to Manager profile IDs.
- Session creation, expiration, idle timeout, and stop lifecycle.
- Short-lived viewer tokens stored only as hashes.
- URL policy validation before any remote navigation.
- Encrypted storage for target URLs and proxy credentials.
- Privacy-preserving audit events.
- CDP automation through Playwright using the Manager CDP endpoint.
- Authenticated viewer pages at `/session/{viewer_token}`.
- Internal proxy routes for Manager's noVNC and clipboard endpoints.
- Public reverse proxy configuration that exposes only Gateway routes.

## Request Flow

1. User opens the Gateway frontend.
2. User submits a target URL and optional Gateway profile ID.
3. Backend validates URL scheme, DNS/IP policy, user limits, and profile ownership.
4. Backend creates or reuses a Gateway profile.
5. Backend creates or updates the corresponding Manager profile through `/api/profiles`.
6. Backend launches the Manager profile through `/api/profiles/{manager_profile_id}/launch`.
7. Backend stores a session row with encrypted target URL and hashed viewer token.
8. Backend connects Playwright to `http://cloakbrowser-manager:8080/api/profiles/{manager_profile_id}/cdp`.
9. Backend opens the target URL in the remote CloakBrowser page.
10. Frontend receives `/session/{viewer_token}` and navigates there.
11. The viewer page validates the token through Gateway APIs.
12. The viewer loads noVNC against a Gateway-authenticated WebSocket path that proxies to Manager `/api/profiles/{manager_profile_id}/vnc`.

The target URL is never placed in the local browser query string.

## Service Boundaries

Public traffic:

- `/`
- `/api/rbi/*`
- `/session/{viewer_token}`
- `/viewer-ws/{viewer_token}`

Internal Docker-only traffic:

- `rbi-gateway-backend -> cloakbrowser-manager:8080`
- `rbi-gateway-backend -> postgres:5432`
- `rbi-gateway-backend -> redis:6379`

The Manager service uses `expose: 8080` only. It must not publish `ports`.

## Data Model

The Gateway owns PostgreSQL tables for:

- `users`
- `rbi_profiles`
- `rbi_sessions`
- `audit_events`

Manager owns its own SQLite profile database and browser profile directories under `/data`. The Gateway stores only the `manager_profile_id` mapping and does not modify Manager's SQLite database directly.

## Session Model

MVP constraints:

- One running session per profile.
- Short-lived random viewer token.
- Store only `viewer_token_hash`.
- Stop clears the viewer token hash and marks the session stopped.
- Expiry and idle timeout are enforced by the backend.
- Target URLs are encrypted at rest or, for early local MVP, kept out of logs and isolated in the database field intended for encrypted values.

## URL Policy

The backend validates every submitted navigation target before CDP navigation.

Blocked schemes:

- `file:`
- `chrome:`
- `devtools:`
- `about:`
- `javascript:`
- `data:`

Blocked destinations:

- localhost names.
- loopback ranges.
- RFC1918 IPv4 ranges.
- link-local ranges.
- IPv6 loopback, unique-local, and link-local ranges.
- cloud metadata addresses such as `169.254.169.254`.

The policy must be applied at session creation and later navigation.

## CDP Automation

Gateway CDP service uses Playwright `chromium.connect_over_cdp()` against the Manager CDP proxy URL.

Required operations:

- `open_url(session_id, target_url)`
- `reload(session_id)`
- `go_back(session_id)`
- `go_forward(session_id)`
- `get_page_title(session_id)`

The CDP endpoint is never returned to the frontend.

## Viewer Strategy

MVP frontend will reuse the Manager noVNC pattern:

- Dynamic import of `@novnc/novnc/core/rfb.js`.
- Connect to a Gateway WebSocket URL derived from the viewer token.
- Gateway validates the viewer token and session state.
- Gateway proxies WebSocket frames to Manager `/api/profiles/{manager_profile_id}/vnc`.

This preserves Manager's KasmVNC/noVNC compatibility behavior and keeps Manager unreachable from public clients.

## Privacy Logging

Gateway logs must avoid full target URLs.

Rules:

- Do not log request query strings.
- Do not print target URLs in application logs.
- Mask or hash domains for audit records.
- Do not record form input, screenshots, or recordings.
- Do not store proxy passwords in plaintext.

## Security Controls

Required MVP controls:

- Manager, CDP, VNC, PostgreSQL, Redis, and Docker daemon are not public.
- HTTPS/WSS at the public edge.
- WebSocket Upgrade support in Nginx.
- `AUTH_TOKEN` configured for Manager even though it is internal.
- Per-user profile ownership checks.
- Per-profile single running session.
- Viewer token expiry and invalidation on stop.
- Configurable global and per-user running session limits.

## Known Upstream Gap

Manager does not expose a dedicated "viewer URL" endpoint. The Gateway will construct its own viewer URL and proxy VNC by session token.

Manager also returns profile fields including `proxy` and `cdp_url` in its own API response. Because Manager is internal-only, the Gateway will avoid exposing those raw Manager responses to public clients and will return sanitized Gateway schemas instead.
