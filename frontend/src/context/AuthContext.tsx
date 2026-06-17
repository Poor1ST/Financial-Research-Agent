import { createContext, useContext, useState, useEffect, type ReactNode } from "react";
import { loginUser, registerUser, fetchSessions, createSession, deleteSession, fetchSessionMessages, chat, type UserResponse, type SessionResponse, type MessageResponse } from "../api/client";

interface AuthContextType {
  user: UserResponse | null;
  token: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  register: (username: string, email: string, password: string) => Promise<void>;
  logout: () => void;
  sessions: SessionResponse[];
  currentSessionId: string | null;
  setCurrentSessionId: (id: string | null) => void;
  messages: MessageResponse[];
  refreshSessions: () => Promise<void>;
  newSession: () => Promise<void>;
  removeSession: (id: string) => Promise<void>;
  sendMessage: (text: string) => Promise<string>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(() => {
    const params = new URLSearchParams(window.location.search);
    const tokenParam = params.get("token");
    const userBase64 = params.get("user");
    if (tokenParam && userBase64) {
      try {
        const u = JSON.parse(atob(userBase64)) as UserResponse;
        localStorage.setItem("token", tokenParam);
        localStorage.setItem("user", JSON.stringify(u));
        window.history.replaceState({}, "", "/");
        return u;
      } catch { /* ignore and fall through */ }
    }
    const stored = localStorage.getItem("user");
    return stored ? JSON.parse(stored) : null;
  });
  const [token, setToken] = useState<string | null>(() => {
    const params = new URLSearchParams(window.location.search);
    const tokenParam = params.get("token");
    if (tokenParam) return tokenParam;
    return localStorage.getItem("token");
  });
  const [loading] = useState(false);
  const [sessions, setSessions] = useState<SessionResponse[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageResponse[]>([]);

  function storeAuth(t: string, u: UserResponse) {
    localStorage.setItem("token", t);
    localStorage.setItem("user", JSON.stringify(u));
    setToken(t);
    setUser(u);
  }

  function clearAuth() {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    setToken(null);
    setUser(null);
    setSessions([]);
    setCurrentSessionId(null);
    setMessages([]);
  }

  async function login(username: string, password: string) {
    const res = await loginUser(username, password);
    storeAuth(res.access_token, res.user);
  }

  async function register(username: string, email: string, password: string) {
    const res = await registerUser(username, email, password);
    storeAuth(res.access_token, res.user);
  }

  function logout() {
    clearAuth();
  }

  async function refreshSessions() {
    try {
      const list = await fetchSessions();
      setSessions(list);
    } catch { /* ignore */ }
  }

  async function newSession() {
    const s = await createSession();
    setSessions((prev) => [s, ...prev]);
    setCurrentSessionId(s.id);
    setMessages([]);
  }

  async function removeSession(id: string) {
    await deleteSession(id);
    setSessions((prev) => prev.filter((s) => s.id !== id));
    if (currentSessionId === id) {
      setCurrentSessionId(null);
      setMessages([]);
    }
  }

  async function sendMessage(text: string): Promise<string> {
    if (!currentSessionId) throw new Error("No active session");
    const res = await chat(text, currentSessionId);
    setMessages((prev) => [
      ...prev,
      { id: 0, session_id: currentSessionId, role: "user", content: text, timestamp: new Date().toISOString() },
      { id: 0, session_id: currentSessionId, role: "assistant", content: res.response, timestamp: new Date().toISOString() },
    ]);
    refreshSessions();
    return res.response;
  }

  useEffect(() => {
    if (token) {
      refreshSessions();
    }
  }, [token]);

  useEffect(() => {
    if (currentSessionId) {
      fetchSessionMessages(currentSessionId).then(setMessages).catch(() => setMessages([]));
    }
  }, [currentSessionId]);

  return (
    <AuthContext.Provider value={{
      user, token, loading, login, register, logout,
      sessions, currentSessionId, setCurrentSessionId,
      messages, refreshSessions, newSession, removeSession, sendMessage,
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
