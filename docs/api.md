# API

## Create Session

`POST /api/rbi/sessions`

```json
{
  "target_url": "https://example.com",
  "profile_id": null,
  "mode": "persistent",
  "ttl_minutes": 60
}
```

Response:

```json
{
  "session_id": "...",
  "viewer_url": "/session/{viewer_token}",
  "expires_at": "...",
  "status": "running"
}
```

The target URL is never included in `viewer_url`.

## Navigate

`POST /api/rbi/sessions/{session_id}/navigate`

```json
{
  "target_url": "https://example.com/new-page"
}
```

Navigation is executed by the backend over CDP. The local browser does not navigate to the target site.

## Toolbar Commands

- `POST /api/rbi/sessions/{session_id}/back`
- `POST /api/rbi/sessions/{session_id}/forward`
- `POST /api/rbi/sessions/{session_id}/reload`
- `POST /api/rbi/sessions/{session_id}/stop`

## Profiles

- `GET /api/rbi/profiles`
- `POST /api/rbi/profiles`
- `GET /api/rbi/profiles/{profile_id}`
- `PATCH /api/rbi/profiles/{profile_id}`
- `DELETE /api/rbi/profiles/{profile_id}`

Gateway profile responses are sanitized and do not expose Manager CDP endpoints.
