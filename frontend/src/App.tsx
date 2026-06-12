import { useState } from "react";
import ThemeToggle from "./components/ThemeToggle";
import ChatView from "./components/ChatView";
import { chat, ingest } from "./api/client";

export type Message = { role: "user" | "assistant"; content: string };

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSend(text: string) {
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);
    setError(null);
    try {
      const { response } = await chat(text);
      setMessages((prev) => [...prev, { role: "assistant", content: response }]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const result = await ingest(file);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `\u{1F4C4} Ingested \`${result.filename}\` \u2014 ${result.chunks_ingested} chunks indexed. You can now query these documents.`,
        },
      ]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-layout">
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

      <ChatView
        messages={messages}
        loading={loading}
        error={error}
        onSend={handleSend}
        onDismissError={() => setError(null)}
      />
    </div>
  );
}
