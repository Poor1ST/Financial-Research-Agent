import { useState, useRef, useEffect } from "react";
import ChatView from "./components/ChatView";
import { chat, ingest } from "./api/client";

type Message = { role: "user" | "assistant"; content: string };

export default function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

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
          content: `📄 Ingested \`${result.filename}\` — ${result.chunks_ingested} chunks indexed. You can now query these documents.`,
        },
      ]);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setLoading(false);
      e.target.value = "";
    }
  }

  return (
    <div style={{ maxWidth: 800, margin: "0 auto", padding: 24 }}>
      <h1>Financial Research Agent</h1>
      <div style={{ marginBottom: 12 }}>
        <input
          type="file"
          accept=".pdf"
          onChange={handleFileUpload}
          disabled={loading}
        />
        <span style={{ marginLeft: 8, fontSize: 12, color: "#666" }}>
          Upload a PDF to add to the knowledge base
        </span>
      </div>
      <ChatView messages={messages} loading={loading} onSend={handleSend} />
      {error && (
        <div style={{ color: "red", marginTop: 8, fontSize: 14 }}>{error}</div>
      )}
    </div>
  );
}
