const API_BASE = "/api";

function authHeaders(): Record<string, string> {
  const token = localStorage.getItem("token");
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  return headers;
}

export async function chat(message: string, sessionId: string) {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ message, session_id: sessionId }),
  });
  if (res.status === 401) { localStorage.removeItem("token"); localStorage.removeItem("user"); window.location.reload(); }
  if (!res.ok) throw new Error(`Chat failed: ${res.status}`);
  return res.json() as Promise<{ response: string }>;
}

export async function ingest(file: File) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/ingest`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) throw new Error(`Ingest failed: ${res.status}`);
  return res.json() as Promise<{ status: string; chunks_ingested: number; filename: string }>;
}

export async function guestChat(message: string, history?: { role: string; content: string }[]) {
  const body: Record<string, unknown> = { message };
  if (history?.length) body.history = history;
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Chat failed: ${res.status}`);
  return res.json() as Promise<{ response: string }>;
}

export type ChartPeriod = "1mo" | "3mo" | "6mo" | "1y";

export interface DataPoint {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  rsi: number | null;
  sma20: number | null;
  sma50: number | null;
  macd: number | null;
  macd_signal: number | null;
  macd_hist: number | null;
  bb_upper: number | null;
  bb_middle: number | null;
  bb_lower: number | null;
}

export interface ChartResponse {
  type: "chart_data";
  ticker: string;
  name: string;
  period: string;
  data: DataPoint[];
}

export async function fetchChartData(ticker: string, period: ChartPeriod = "6mo"): Promise<ChartResponse> {
  const params = new URLSearchParams({ ticker, period });
  const res = await fetch(`${API_BASE}/chart?${params}`);
  if (!res.ok) throw new Error(`Chart fetch failed: ${res.status}`);
  return res.json();
}

export interface UserResponse {
  id: number;
  username: string;
  email: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserResponse;
}

export interface SessionResponse {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface MessageResponse {
  id: number;
  session_id: string;
  role: string;
  content: string;
  timestamp: string;
}

async function authFetch(url: string, options?: RequestInit): Promise<Response> {
  const token = localStorage.getItem("token");
  const res = await fetch(url, {
    ...options,
    headers: {
      ...options?.headers,
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });
  if (res.status === 401) { localStorage.removeItem("token"); localStorage.removeItem("user"); window.location.reload(); }
  return res;
}

export async function registerUser(email: string, password: string): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || "Registration failed");
  return res.json();
}

export async function loginUser(email: string, password: string): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || "Login failed");
  return res.json();
}

export async function fetchSessions(): Promise<SessionResponse[]> {
  const res = await authFetch(`${API_BASE}/auth/sessions`);
  if (!res.ok) throw new Error("Failed to fetch sessions");
  return res.json();
}

export async function createSession(): Promise<SessionResponse> {
  const res = await authFetch(`${API_BASE}/auth/sessions`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to create session");
  return res.json();
}

export async function deleteSession(sessionId: string): Promise<void> {
  const res = await authFetch(`${API_BASE}/auth/sessions/${sessionId}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Failed to delete session");
}

export async function fetchSessionMessages(sessionId: string): Promise<MessageResponse[]> {
  const res = await authFetch(`${API_BASE}/auth/sessions/${sessionId}/messages`);
  if (!res.ok) throw new Error("Failed to fetch messages");
  return res.json();
}
