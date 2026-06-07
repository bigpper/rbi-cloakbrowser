import { FormEvent, useEffect, useState } from "react";
import { api, DisplayProfile, Profile } from "../api/client";

export function Home() {
  const [targetUrl, setTargetUrl] = useState("https://example.com");
  const [profileId, setProfileId] = useState("");
  const [displayProfile, setDisplayProfile] = useState<DisplayProfile>("high");
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.listProfiles().then(setProfiles).catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    async function chooseInitialDisplayProfile() {
      const startedAt = performance.now();
      try {
        await fetch("/api/rbi/health", { cache: "no-store" });
        const rtt = performance.now() - startedAt;
        if (rtt > 600) setDisplayProfile("low");
        else if (rtt > 250) setDisplayProfile("medium");
      } catch {
        setDisplayProfile("medium");
      }
    }

    chooseInitialDisplayProfile();
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      const session = await api.createSession(targetUrl, profileId || undefined, displayProfile);
      sessionStorage.setItem(`rbi-session:${session.viewer_url}`, session.session_id);
      window.location.href = session.viewer_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create session");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="container">
      <div className="card">
        <h1>RBI Gateway</h1>
        <p className="muted">目标网站只会由远程 CloakBrowser 访问，本地浏览器只打开 Gateway session viewer。</p>
        <form onSubmit={submit}>
          <div className="row">
            <input
              className="field"
              value={targetUrl}
              onChange={(event) => setTargetUrl(event.target.value)}
              placeholder="https://example.com"
            />
            <select className="field" value={profileId} onChange={(event) => setProfileId(event.target.value)}>
              <option value="">自动创建 profile</option>
              {profiles.map((profile) => (
                <option key={profile.id} value={profile.id}>
                  {profile.name}
                </option>
              ))}
            </select>
            <select
              className="field compact"
              value={displayProfile}
              onChange={(event) => setDisplayProfile(event.target.value as DisplayProfile)}
            >
              <option value="high">高清 1280x720</option>
              <option value="medium">均衡 1024x576</option>
              <option value="low">低带宽 854x480</option>
            </select>
            <button className="button" disabled={loading}>
              {loading ? "启动中..." : "打开远程浏览器"}
            </button>
          </div>
        </form>
        {error && <p className="error">{error}</p>}
      </div>
    </main>
  );
}
