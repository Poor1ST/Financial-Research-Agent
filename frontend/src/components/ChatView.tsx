import { useRef, useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import rehypeSanitize from "rehype-sanitize";
import type { Message } from "../App";

interface Props {
  messages: Message[];
  loading: boolean;
  error: string | null;
  onSend: (text: string) => void;
  onDismissError: () => void;
}

const HINTS = [
  "What's AAPL's current price and RSI?",
  "Analyze TSLA with technical indicators",
  "Search financial news for oil prices",
  "Give me a full analysis report on MSFT",
  "What's the market outlook for gold?",
];

export default function ChatView({ messages, loading, error, onSend, onDismissError }: Props) {
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || loading) return;
    onSend(input.trim());
    setInput("");
  }

  function handleHint(hint: string) {
    onSend(hint);
  }

  const hasMessages = messages.length > 0;

  return (
    <>
      <div className="chat-area">
        {!hasMessages && !loading && (
          <div className="empty-state">
            <div className="empty-state-icon">{"\uD83D\uDCCA"}</div>
            <h2>Financial Research Terminal</h2>
            <p>Ask about any stock, commodity, or market condition. Get real-time data, technical analysis, and structured reports to support your decisions.</p>
            <div className="empty-state-hints">
              {HINTS.map((hint) => (
                <button key={hint} className="hint-chip" onClick={() => handleHint(hint)}>
                  {hint}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`message-row ${msg.role}`}>
            <div className="message-bubble">
              {msg.role === "assistant" ? (
                <ReactMarkdown rehypePlugins={[rehypeSanitize]}>
                  {msg.content}
                </ReactMarkdown>
              ) : (
                msg.content
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="message-row assistant">
            <div className="loading-dots">
              Synthesizing data<span>.</span><span>.</span><span>.</span>
            </div>
          </div>
        )}

        {error && (
          <div className="error-bar">
            {error}
            <button
              onClick={onDismissError}
              style={{ background: "none", border: "none", color: "inherit", marginLeft: 12, cursor: "pointer", fontWeight: 600 }}
            >
              Dismiss
            </button>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <form className="input-bar" onSubmit={handleSubmit}>
        <div className="input-bar-left">
          <label className="attach-btn" title="Upload PDF">
            <input
              type="file"
              accept=".pdf"
              style={{ display: "none" }}
              disabled={loading}
            />
            {"\uD83D\uDCCE"}
          </label>
        </div>
        <input
          ref={inputRef}
          className="input-bar-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about a stock, commodity, or market condition..."
          disabled={loading}
        />
        <button
          type="submit"
          className="send-btn"
          disabled={loading || !input.trim()}
        >
          {loading ? "Analyzing..." : "Send"}
        </button>
      </form>
    </>
  );
}
