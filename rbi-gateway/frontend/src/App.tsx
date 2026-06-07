import { Home } from "./pages/Home";
import { ProfileList } from "./pages/ProfileList";
import { SessionViewer } from "./pages/SessionViewer";

export default function App() {
  const path = window.location.pathname;

  if (path.startsWith("/session/")) {
    return <SessionViewer />;
  }

  if (path === "/profiles") {
    return (
      <div className="app-shell">
        <Nav />
        <ProfileList />
      </div>
    );
  }

  return (
    <div className="app-shell">
      <Nav />
      <Home />
    </div>
  );
}

function Nav() {
  return (
    <div className="topbar">
      <strong>RBI Gateway</strong>
      <a className="muted" href="/">
        Home
      </a>
      <a className="muted" href="/profiles">
        Profiles
      </a>
    </div>
  );
}
