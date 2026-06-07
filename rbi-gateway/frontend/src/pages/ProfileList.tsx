import { FormEvent, useEffect, useState } from "react";
import { api, Profile } from "../api/client";

export function ProfileList() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [name, setName] = useState("Default RBI Profile");
  const [error, setError] = useState("");

  async function refresh() {
    setProfiles(await api.listProfiles());
  }

  useEffect(() => {
    refresh().catch((err) => setError(err.message));
  }, []);

  async function create(event: FormEvent) {
    event.preventDefault();
    try {
      await api.createProfile(name);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create profile");
    }
  }

  async function remove(id: string) {
    await api.deleteProfile(id);
    await refresh();
  }

  return (
    <main className="container">
      <div className="card">
        <h1>Profiles</h1>
        <form className="row" onSubmit={create}>
          <input className="field" value={name} onChange={(event) => setName(event.target.value)} />
          <button className="button">创建 profile</button>
        </form>
        {error && <p className="error">{error}</p>}
        {profiles.map((profile) => (
          <div className="row" key={profile.id} style={{ marginTop: 12 }}>
            <div style={{ flex: 1 }}>
              <strong>{profile.name}</strong>
              <div className="muted">{profile.id}</div>
            </div>
            <button className="button danger" onClick={() => remove(profile.id)}>
              删除
            </button>
          </div>
        ))}
      </div>
    </main>
  );
}
