import { useRef, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";

type Message = { role: "user" | "assistant"; content: string };

interface Props {
  messages: Message[];
  loading: boolean;
  onSend: (text: string) => void;
}

export default function ChatView({ messages, loading, onSend }: Props) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;
    onSend(input.trim());
    setInput("");
  }

  return (
    <div
      style={{
        border: "1px solid #ddd",
        borderRadius: 8,
        display: "flex",
        flexDirection: "column",
        height: 500,
      }}
    >
      <div style={{ flex: 1, overflowY: "auto", padding: 16 }}>
        {messages.length === 0 && (
          <p style={{ color: "#888", textAlign: "center" }}>
            Ask about a stock, upload a PDF, or request an analysis report.
          </p>
        )}
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              marginBottom: 12,
              textAlign: msg.role === "user" ? "right" : "left",
            }}
          >
            <div
              style={{
                display: "inline-block",
                padding: "8px 14px",
                borderRadius: 12,
                background: msg.role === "user" ? "#007bff" : "#f0f0f0",
                color: msg.role === "user" ? "#fff" : "#000",
                maxWidth: "80%",
                textAlign: "left",
              }}
            >
              <ReactMarkdown rehypePlugins={[rehypeSanitize]}>
                {msg.content}
              </ReactMarkdown>
            </div>
          </div>
        ))}
        {loading && (
          <div style={{ color: "#888", fontStyle: "italic" }}>Thinking...</div>
        )}
        <div ref={bottomRef} />
      </div>
      <form
        onSubmit={handleSubmit}
        style={{ display: "flex", borderTop: "1px solid #ddd", padding: 8 }}
      >
        <input
          ref={(el) => el?.focus()}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about a stock..."
          disabled={loading}
          style={{ flex: 1, padding: 8, borderRadius: 4, border: "1px solid #ccc" }}
        />
        <button
          type="submit"
          disabled={loading || !input.trim()}
          style={{
            marginLeft: 8,
            padding: "8px 16px",
            borderRadius: 4,
            border: "none",
            background: loading ? "#ccc" : "#007bff",
            color: "#fff",
            cursor: loading ? "not-allowed" : "pointer",
          }}
        >
          Send
        </button>
      </form>
    </div>
  );
}
