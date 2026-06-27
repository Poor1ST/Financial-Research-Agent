import { useAuth } from "../context/AuthContext";

export default function SessionSidebar({
  setGuestMessages,
  setShowAuthModal,
}: {
  setGuestMessages: (m: { role: "user" | "assistant"; content: string }[]) => void;
  setShowAuthModal: (v: boolean) => void;
}) {
  const { user, sessions, currentSessionId, setCurrentSessionId, newSession, removeSession, logout } = useAuth();

  function formatDate(iso: string) {
    const d = new Date(iso);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    if (diff < 86400000) return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    if (diff < 604800000) return d.toLocaleDateString([], { weekday: "short" });
    return d.toLocaleDateString([], { month: "short", day: "numeric" });
  }

  return (
    <aside className="sidebar">
      <button
        className="sidebar-new-chat"
        onClick={() => {
          if (user) {
            newSession();
          } else {
            setGuestMessages([]);
          }
        }}
      >
        + New Chat
      </button>

      <div className="sidebar-sessions">
        {user ? (
          sessions.map((s) => (
            <div
              key={s.id}
              className={`sidebar-session ${s.id === currentSessionId ? "active" : ""}`}
              onClick={() => setCurrentSessionId(s.id)}
            >
              <div className="sidebar-session-title">{s.title}</div>
              <div className="sidebar-session-date">{formatDate(s.updated_at)}</div>
              <button
                className="sidebar-session-delete"
                onClick={(e) => { e.stopPropagation(); removeSession(s.id); }}
                title="Delete session"
              >
                ×
              </button>
            </div>
          ))
        ) : (
          <div className="sidebar-guest-placeholder">
            <p>Sign in to save your chat history and access your sessions.</p>
          </div>
        )}
      </div>

      <div className="sidebar-footer">
        {user ? (
          <>
            <div className="sidebar-user">{user.username}</div>
            <button className="sidebar-logout" onClick={logout}>Log out</button>
          </>
        ) : (
          <button className="sidebar-login-btn" onClick={() => setShowAuthModal(true)}>
            Sign in
          </button>
        )}
      </div>
    </aside>
  );
}