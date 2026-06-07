import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { api, DisplayProfile } from "../api/client";

export function SessionViewer() {
  const viewerToken = useMemo(() => window.location.pathname.split("/").pop() || "", []);
  const sessionId = sessionStorage.getItem(`rbi-session:/session/${viewerToken}`) || "";
  const containerRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement>(null);
  const [connected, setConnected] = useState(false);
  const [targetUrl, setTargetUrl] = useState("");
  const [localText, setLocalText] = useState("");
  const [displayProfile, setDisplayProfile] = useState<DisplayProfile>("high");
  const [toolbarOpen, setToolbarOpen] = useState(true);
  const [audioEnabled, setAudioEnabled] = useState(false);
  const [audioStatus, setAudioStatus] = useState("muted");
  const [networkQuality, setNetworkQuality] = useState<"good" | "fair" | "poor">("good");
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
        rfb.addEventListener("bell", () => setNetworkQuality("fair"));
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

  useEffect(() => {
    if (!audioEnabled || !audioRef.current) {
      setAudioStatus("muted");
      return;
    }

    const audio = audioRef.current;
    const mediaSource = new MediaSource();
    const audioUrl = URL.createObjectURL(mediaSource);
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const socket = new WebSocket(`${protocol}//${window.location.host}/audio-ws/${viewerToken}`);
    const queue: ArrayBuffer[] = [];
    let sourceBuffer: SourceBuffer | null = null;
    let closed = false;

    function pump() {
      if (!sourceBuffer || sourceBuffer.updating || !queue.length) return;
      sourceBuffer.appendBuffer(queue.shift() as ArrayBuffer);
    }

    audio.src = audioUrl;
    audio.autoplay = true;
    audio.play().catch(() => setAudioStatus("click to play"));
    socket.binaryType = "arraybuffer";
    socket.onopen = () => setAudioStatus("connecting audio");
    socket.onerror = () => setAudioStatus("audio unavailable");
    socket.onclose = () => {
      if (!closed) setAudioStatus("audio disconnected");
    };
    socket.onmessage = (event) => {
      if (event.data instanceof ArrayBuffer) {
        queue.push(event.data);
        pump();
      }
    };
    mediaSource.addEventListener("sourceopen", () => {
      sourceBuffer = mediaSource.addSourceBuffer('audio/webm; codecs="opus"');
      sourceBuffer.addEventListener("updateend", pump);
      setAudioStatus("audio on");
      pump();
    });

    return () => {
      closed = true;
      socket.close();
      audio.pause();
      audio.removeAttribute("src");
      URL.revokeObjectURL(audioUrl);
    };
  }, [audioEnabled, viewerToken]);

  useEffect(() => {
    let cancelled = false;

    async function sampleNetwork() {
      const startedAt = performance.now();
      try {
        await fetch("/api/rbi/health", { cache: "no-store" });
        if (cancelled) return;
        const rtt = performance.now() - startedAt;
        if (rtt > 600) setNetworkQuality("poor");
        else if (rtt > 250) setNetworkQuality("fair");
        else setNetworkQuality("good");
      } catch {
        if (!cancelled) setNetworkQuality("poor");
      }
    }

    sampleNetwork();
    const interval = window.setInterval(sampleNetwork, 10_000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

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

  async function submitLocalText(event: FormEvent) {
    event.preventDefault();
    if (!sessionId || !localText.trim()) return;
    try {
      await api.insertText(sessionId, localText);
      setLocalText("");
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "文本注入失败");
    }
  }

  async function changeDisplayProfile(nextProfile: DisplayProfile) {
    setDisplayProfile(nextProfile);
    if (!sessionId) return;
    try {
      await api.setDisplayProfile(sessionId, nextProfile);
      setError("显示档位已记录；当前 VNC geometry 需要新建/重启 session 后完全生效。");
    } catch (err) {
      setError(err instanceof Error ? err.message : "显示档位切换失败");
    }
  }

  async function stop() {
    if (!sessionId) return;
    await api.stopSession(sessionId);
    window.location.href = "/";
  }

  return (
    <div className="viewer-layout">
      <button className="toolbar-toggle" onClick={() => setToolbarOpen((open) => !open)}>
        {toolbarOpen ? "隐藏控制栏" : "显示控制栏"}
      </button>
      {toolbarOpen && (
        <div className="viewer-toolbar">
          <div className="viewer-toolbar-line">
            <strong>RBI Viewer</strong>
            <span className={`status-dot ${connected ? "online" : ""}`} />
            <span className="muted">{connected ? "connected" : "connecting"}</span>
            <span className={`quality ${networkQuality}`}>网络：{networkQuality}</span>
            <select
              className="field compact"
              value={displayProfile}
              onChange={(event) => changeDisplayProfile(event.target.value as DisplayProfile)}
            >
              <option value="high">高清 1280x720</option>
              <option value="medium">均衡 1024x576</option>
              <option value="low">低带宽 854x480</option>
            </select>
            <button className="button secondary" onClick={() => setAudioEnabled((enabled) => !enabled)}>
              {audioEnabled ? "关闭声音" : "开启声音"}
            </button>
            <button className="button danger" onClick={stop}>
              关闭 session
            </button>
          </div>
          <form className="viewer-toolbar-line" onSubmit={navigate}>
            <input
              className="field"
              value={targetUrl}
              onChange={(event) => setTargetUrl(event.target.value)}
              placeholder="https://example.com/new-page"
            />
            <button className="button">导航</button>
            <button className="button secondary" type="button" onClick={() => api.back(sessionId).catch(() => undefined)}>
              后退
            </button>
            <button className="button secondary" type="button" onClick={() => api.forward(sessionId).catch(() => undefined)}>
              前进
            </button>
            <button className="button secondary" type="button" onClick={() => api.reload(sessionId).catch(() => undefined)}>
              刷新
            </button>
          </form>
          <form className="viewer-toolbar-line" onSubmit={submitLocalText}>
            <input
              className="field"
              value={localText}
              onChange={(event) => setLocalText(event.target.value)}
              placeholder="本地输入中文/任意文本，确认后注入远程焦点"
            />
            <button className="button secondary">发送文本</button>
          </form>
          {audioEnabled && <p className="muted audio-hint">声音通道已请求；浏览器会在用户点击后允许播放远程音频。</p>}
        </div>
      )}
      {error && <div className="topbar error">{error}</div>}
      <audio ref={audioRef} hidden />
      {audioEnabled && <div className="audio-status">{audioStatus}</div>}
      <div
        className="viewer-canvas"
        ref={containerRef}
        onMouseMove={() => {
          if (!connected) setNetworkQuality("poor");
        }}
      />
    </div>
  );
}
