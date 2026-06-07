# Security

## Public Exposure

Only the Gateway Nginx service should publish ports:

- `80`
- `443`

Do not publish:

- `cloakbrowser-manager:8080`
- CDP ports
- VNC ports
- PostgreSQL
- Redis
- Docker daemon

`cloakbrowser-manager` is configured with `expose: 8080` only, so it is reachable by Docker-internal services but not public clients.

## Viewer Tokens

Session viewer URLs use `/session/{viewer_token}`. The target URL is not placed in query strings. The backend stores only a hash of the viewer token and invalidates it when the session is stopped or expired.

## URL Policy

The backend rejects unsafe schemes and local/private targets before navigation. Blocked schemes include `file:`, `chrome:`, `devtools:`, `about:`, `javascript:`, and `data:`.

## Logging

Nginx uses `$uri` instead of `$request_uri`, so query strings are not written to access logs. Application code should use `privacy_log_service.mask_url_for_log()` and `domain_hash()` rather than logging full target URLs.

## Production Auth

The current MVP includes a demo user shim through `X-User-Id`. Replace it with real authentication before internet exposure.

## Manager Auth

Set `CLOAK_MANAGER_AUTH_TOKEN` in `.env`. Gateway calls Manager with `Authorization: Bearer <token>`.
