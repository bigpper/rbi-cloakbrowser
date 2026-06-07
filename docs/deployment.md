# Deployment

## Local MVP

```bash
cp .env.example .env
docker compose up --build
```

Open `http://localhost`.

The bundled Nginx command generates a self-signed development certificate if no certificate exists. For production, replace it with a real certificate mounted at:

- `/etc/nginx/certs/fullchain.pem`
- `/etc/nginx/certs/privkey.pem`

## HTTPS / WSS

Terminate TLS at Nginx, Caddy, or an upstream load balancer. WebSocket paths must preserve Upgrade headers for `/viewer-ws/`.

Required proxy headers:

```nginx
proxy_set_header Host $host;
proxy_set_header X-Forwarded-Proto https;
proxy_set_header Upgrade $http_upgrade;
proxy_set_header Connection $connection_upgrade;
```

## Ports

Public:

- `80`
- `443`

Internal only:

- `rbi-gateway-backend:8000`
- `rbi-gateway-frontend:80`
- `cloakbrowser-manager:8080`
- `postgres:5432`
- `redis:6379`

## Verify Local Browser Isolation

1. Open browser developer tools on the Gateway page.
2. Create a session for `https://example.com`.
3. Confirm the address bar changes to `/session/{viewer_token}` only.
4. In the Network tab, verify requests go to the Gateway origin, not directly to `example.com`.
5. Confirm remote navigation is performed through `POST /api/rbi/sessions/{session_id}/navigate`.

## Persistent Profiles

Manager profile data is stored in the Docker volume `cloakprofiles`. Cookies, localStorage, cache, and session data survive browser restarts as long as this volume is preserved.
