import { useState, useCallback, useEffect } from "react";
import { useAuth } from "./context/AuthContext";
import { guestChat, ingest } from "./api/client";
import ThemeToggle from "./components/ThemeToggle";
import ChatView from "./components/ChatView";
import AuthModal from "./components/AuthModal";
import SessionSidebar from "./components/SessionSidebar";

export type Message = { role: "user" | "assistant"; content: string };

function MainApp({
  guestMessages,
  setGuestMessages,
  setShowAuthModal,
}: {
  guestMessages: Message[];
  setGuestMessages: React.Dispatch<React.SetStateAction<Message[]>>;
  setShowAuthModal: (v: boolean) => void;
}) {
  const { user, currentSessionId, messages, sendMessage } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadMessages, setUploadMessages] = useState<Message[]>([]);

  useEffect(() => { setUploadMessages([]); }, [currentSessionId]);

  const handleSend = useCallback(async (text: string) => {
    setLoading(true);
    setError(null);
    try {
      if (user) {
        await sendMessage(text);
      } else {
        const history = guestMessages.map((m) => ({ role: m.role, content: m.content }));
        const res = await guestChat(text, history);
        setGuestMessages((prev) => [
          ...prev,
          { role: "user", content: text },
          { role: "assistant", content: res.response },
        ]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }, [user, sendMessage, guestMessages, setGuestMessages]);

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const result = await ingest(file);
      setUploadMessages((prev) => [
        ...prev,
        { role: "assistant", content: `\u{1F4C4} Ingested \`${result.filename}\` — ${result.chunks_ingested} chunks indexed.` },
      ]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  const chatMessages: Message[] = user
    ? [...uploadMessages, ...messages.map((m) => ({ role: m.role as "user" | "assistant", content: m.content }))]
    : [...uploadMessages, ...guestMessages];

  return (
    <div className="app-with-sidebar">
      <SessionSidebar
        setGuestMessages={setGuestMessages}
        setShowAuthModal={setShowAuthModal}
      />
      <div className="main-content">
        <header className="header">
          <div className="header-left">
            <div className="header-logo">F</div>
            <span className="header-title">Financial Research Terminal</span>
          </div>
          <div className="header-right">
            <label className="upload-btn" title="Upload PDF">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileUpload}
                disabled={loading}
                style={{ display: "none" }}
              />
              {"\uD83D\uDCCE"}<span> Upload PDF</span>
            </label>
            <ThemeToggle />
          </div>
        </header>

        {user && !currentSessionId ? (
          <div className="empty-state">
            <div className="empty-state-icon">{"\uD83D\uDCCA"}</div>
            <h2>Select or create a chat session</h2>
            <p>Choose a session from the sidebar or click "+ New Chat" to get started.</p>
          </div>
        ) : (
          <ChatView
            messages={chatMessages}
            loading={loading}
            error={error}
            onSend={handleSend}
            onDismissError={() => setError(null)}
          />
        )}
      </div>
    </div>
  );
}

export default function App() {
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [guestMessages, setGuestMessages] = useState<Message[]>([]);

  return (
    <>
      <MainApp
        guestMessages={guestMessages}
        setGuestMessages={setGuestMessages}
        setShowAuthModal={setShowAuthModal}
      />
      {showAuthModal && <AuthModal onClose={() => setShowAuthModal(false)} />}
    </>
  );
}