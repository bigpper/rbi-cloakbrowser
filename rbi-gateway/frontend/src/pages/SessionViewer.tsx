import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";

export function SessionViewer() {
  const viewerToken = useMemo(() => window.location.pathname.split("/").pop() || "", []);
  const sessionId = sessionStorage.getItem(`rbi-session:/session/${viewerToken}`) || "";
  const containerRef = useRef<HTMLDivElement>(null);
  const [connected, setConnected] = useState(false);
  const [targetUrl, setTargetUrl] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let rfb: import("@novnc/novnc").default | null = null;
    let cancelled = false;

    async function connect() {
      try {
        const { default: RFB } = await import("@novnc/novnc");
        if (!containerRef.current || cancelled) return;
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        rfb = new RFB(containerRef.current, `${protocol}//${window.location.host}/viewer-ws/${viewerToken}`, {
          wsProtocols: ["binary"],
        });
        rfb.scaleViewport = true;
        rfb.resizeSession = false;
        rfb.showDotCursor = true;
        rfb.addEventListener("connect", () => setConnected(true));
        rfb.addEventListener("disconnect", () => setConnected(false));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to connect viewer");
      }
    }

    connect();
    return () => {
      cancelled = true;
      rfb?.disconnect();
    };
  }, [viewerToken]);

  async function navigate(event: FormEvent) {
    event.preventDefault();
    if (!sessionId) {
      setError("Missing session id in local session state. Create the session from Home again.");
      return;
    }
    try {
      await api.navigate(sessionId, targetUrl);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Navigation failed");
    }
  }

  async function stop() {
    if (!sessionId) return;
    await api.stopSession(sessionId);
    window.location.href = "/";
  }

  return (
    <div className="viewer-layout">
      <div className="topbar">
        <strong>Session Viewer</strong>
        <span className="muted">{connected ? "connected" : "connecting"}</span>
        <form className="row" onSubmit={navigate} style={{ flex: 1 }}>
          <input
            className="field"
            value={targetUrl}
            onChange={(event) => setTargetUrl(event.target.value)}
            placeholder="https://example.com/new-page"
          />
          <button className="button">导航</button>
        </form>
        <button className="button secondary" onClick={() => api.back(sessionId).catch(() => undefined)}>
          后退
        </button>
        <button className="button secondary" onClick={() => api.forward(sessionId).catch(() => undefined)}>
          前进
        </button>
        <button className="button secondary" onClick={() => api.reload(sessionId).catch(() => undefined)}>
          刷新
        </button>
        <button className="button danger" onClick={stop}>
          关闭 session
        </button>
      </div>
      {error && <div className="topbar error">{error}</div>}
      <div className="viewer-canvas" ref={containerRef} />
    </div>
  );
}
