import { useState } from "react";
import { NavLink, Route, Routes, useLocation } from "react-router-dom";
import FeedPage from "./pages/FeedPage";
import ChatPage from "./pages/ChatPage";
import ModeratorPage from "./pages/ModeratorPage";
import IngestPage from "./pages/IngestPage";
import SidebarRail from "./components/SidebarRail";
import { api } from "./api/client";
import { useViewMode } from "./viewMode";

function HeaderFor({ path }: { path: string }) {
  if (path.startsWith("/mod"))
    return (
      <>
        <span>Moderator queue</span>
        <span className="sub">decisions are audited</span>
      </>
    );
  if (path.startsWith("/chat"))
    return (
      <>
        <span>Counseling session</span>
        <span className="sub">multi-turn · C1/C2 re-checked each turn</span>
      </>
    );
  if (path.startsWith("/ingest"))
    return (
      <>
        <span>Compose a post</span>
        <span className="sub">pipeline demo · synchronous</span>
      </>
    );
  return (
    <>
      <span>Home</span>
      <span className="sub">what users and teammates see</span>
    </>
  );
}

function ViewModeControls() {
  const [mode, setMode] = useViewMode();
  const [busy, setBusy] = useState(false);

  async function onReset() {
    if (!confirm("Reset demo data? This wipes all posts, replies, and sessions, then re-seeds 6 mock posts.")) return;
    setBusy(true);
    try {
      await api.reset();
      window.location.reload();
    } finally {
      setBusy(false);
    }
  }

  const isAdmin = mode === "admin";
  return (
    <div className="mode-switch">
      <div className="row">
        <span>Admin view</span>
        <div
          role="switch"
          aria-checked={isAdmin}
          className={`toggle${isAdmin ? " on" : ""}`}
          onClick={() => setMode(isAdmin ? "user" : "admin")}
        />
      </div>
      <div className="hint">
        {isAdmin
          ? "Showing labels, scores, pipeline metadata."
          : "Clean user feed — click to inspect internals."}
      </div>
      <div className="row" style={{ marginTop: 12 }}>
        <button className="btn small ghost" onClick={onReset} disabled={busy} style={{ width: "100%", justifyContent: "center" }}>
          {busy ? "Resetting…" : "Reset demo data"}
        </button>
      </div>
    </div>
  );
}

export default function App() {
  const loc = useLocation();
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          MMS
          <span className="tag">Moderation & persuasion prototype</span>
        </div>
        <nav>
          <NavLink to="/" end className={({ isActive }) => (isActive ? "active" : "")}>
            <span className="icon">#</span> Feed
          </NavLink>
          <NavLink to="/ingest" className={({ isActive }) => (isActive ? "active" : "")}>
            <span className="icon">✎</span> Compose
          </NavLink>
          <NavLink to="/mod" className={({ isActive }) => (isActive ? "active" : "")}>
            <span className="icon">⌾</span> Moderator
          </NavLink>
        </nav>
        <ViewModeControls />
      </aside>
      <main className="main">
        <div className="main-header">
          <HeaderFor path={loc.pathname} />
        </div>
        <Routes>
          <Route path="/" element={<FeedPage />} />
          <Route path="/chat/:sessionId" element={<ChatPage />} />
          <Route path="/mod" element={<ModeratorPage />} />
          <Route path="/ingest" element={<IngestPage />} />
        </Routes>
      </main>
      <SidebarRail />
    </div>
  );
}
