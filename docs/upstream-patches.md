# Upstream Patches

No upstream source files under `vendor/CloakBrowser` or `vendor/CloakBrowser-Manager` are modified for the current MVP.

The Gateway integrates CloakBrowser-Manager through its existing public API:

- `/api/profiles`
- `/api/profiles/{profile_id}/launch`
- `/api/profiles/{profile_id}/stop`
- `/api/profiles/{profile_id}/status`
- `/api/profiles/{profile_id}/vnc`
- `/api/profiles/{profile_id}/cdp`

If future work requires Manager changes, keep them as thin adapters and document every changed file here.
