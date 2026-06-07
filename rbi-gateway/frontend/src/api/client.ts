export interface Profile {
  id: string;
  name: string;
  manager_profile_id: string;
  persistent: boolean;
  status: string;
}

export interface CreateSessionResponse {
  session_id: string;
  viewer_url: string;
  expires_at: string;
  status: string;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", "X-User-Id": "demo-user" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || res.statusText);
  }
  return res.json() as Promise<T>;
}

export const api = {
  listProfiles: () => request<Profile[]>("/api/rbi/profiles"),
  createProfile: (name: string) =>
    request<Profile>("/api/rbi/profiles", {
      method: "POST",
      body: JSON.stringify({ name, persistent: true }),
    }),
  deleteProfile: (id: string) =>
    request<{ ok: boolean }>(`/api/rbi/profiles/${id}`, { method: "DELETE" }),
  createSession: (targetUrl: string, profileId?: string) =>
    request<CreateSessionResponse>("/api/rbi/sessions", {
      method: "POST",
      body: JSON.stringify({
        target_url: targetUrl,
        profile_id: profileId || null,
        mode: "persistent",
        ttl_minutes: 60,
      }),
    }),
  navigate: (sessionId: string, targetUrl: string) =>
    request<{ session_id: string; status: string }>(`/api/rbi/sessions/${sessionId}/navigate`, {
      method: "POST",
      body: JSON.stringify({ target_url: targetUrl }),
    }),
  stopSession: (sessionId: string) =>
    request<{ session_id: string; status: string }>(`/api/rbi/sessions/${sessionId}/stop`, {
      method: "POST",
    }),
  reload: (sessionId: string) =>
    request<{ session_id: string; status: string }>(`/api/rbi/sessions/${sessionId}/reload`, {
      method: "POST",
    }),
  back: (sessionId: string) =>
    request<{ session_id: string; status: string }>(`/api/rbi/sessions/${sessionId}/back`, {
      method: "POST",
    }),
  forward: (sessionId: string) =>
    request<{ session_id: string; status: string }>(`/api/rbi/sessions/${sessionId}/forward`, {
      method: "POST",
    }),
};
