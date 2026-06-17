# AGENTS.md — Financial Research Agent

LangChain-based conversational agent. FastAPI backend, Vite+React frontend, ReAct agent with 4 tools, RAG over PDFs.

## Dev commands

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt  # after any dep change
python -m app.main              # uvicorn on :8000

# Frontend
cd frontend
npm install                      # after any dep change
npm run dev                      # vite on :5173, proxies /api to :8000
npm run build                    # tsc + vite build
```

## Project structure

```
backend/app/
├── agent/          # agent.py (ReAct setup), tools.py (4 tools), prompt.py
├── rag/            # ingest.py (PDF → ChromaDB), retriever.py (query ChromaDB)
├── api/
│   ├── auth.py     # POST /register, POST /login, GET /me, GET/POST/DELETE sessions
│   │               # GET /google/login, GET /google/callback (OAuth)
│   └── routes.py   # POST /api/chat, POST /api/ingest, GET /api/health, GET /api/chart
├── models/
│   ├── database.py # User (id, username, email, password_hash, google_id),
│   │               # Session (id, user_id, title), Message (id, session_id, role, content)
│   └── schemas.py  # ChatRequest/Response, AnalysisReport, IngestionResponse,
│                   # UserCreate/Login/Response, TokenResponse, SessionResponse, MessageResponse
└── main.py         # FastAPI app + CORS (two routers: routes + auth)
frontend/src/
├── api/client.ts   # chat(), ingest(), authFetch(), registerUser(), loginUser(), etc.
├── context/
│   ├── AuthContext.tsx  # auth state, sessions, messages, login/register/logout, Google callback
│   └── ThemeContext.tsx
└── components/
    ├── AuthForm.tsx       # login/register form + "Sign in with Google" button
    ├── SessionSidebar.tsx # session list, new/delete, user info, logout
    └── ChatView.tsx       # markdown-rendered chat
```

## Architecture

```
React → /api/chat (auth Bearer token) → FastAPI → ReAct Agent
  ├── Tool: yfinance + pandas-ta (price, RSI, SMA, MACD, Bollinger)
  ├── Tool: DuckDuckGo search (news)
  ├── Tool: ChromaDB retriever (RAG on uploaded PDFs)
  └── LLM: Groq llama3-70b-8192
```

## Auth system

Three login methods:
1. **Register** — POST `/api/auth/register` (username + email + password → bcrypt hashed)
2. **Login** — POST `/api/auth/login` (username/email + password)
3. **Google OAuth** — GET `/api/auth/google/login` → Google consent → redirects to `/?token=...&user=...`

JWT (HS256, 24h expiry) stored in `localStorage`, sent as `Authorization: Bearer` header.
`JWT_SECRET` env var (defaults to `dev-secret-change-in-production`).

### Google OAuth flow

```
AuthForm → clicks "Sign in with Google"
  → GET /api/auth/google/login
  → Redirects to Google consent (with state param for CSRF)
  → User approves → Google redirects to /api/auth/google/callback?code=...&state=...
  → Backend exchanges code for access token (httpx POST to /token)
  → Backend fetches userinfo from Google (GET /oauth2/v2/userinfo)
  → Finds user by google_id or email, creates if new (username from email prefix)
  → Issues app JWT, base64-encodes user info
  → Redirects to FRONTEND_URL/?token=xxx&user=base64
  → AuthContext lazy initializer reads URL params, stores in localStorage
  → App re-renders with authenticated user
```

## Required env vars

```env
GROQ_API_KEY=<from console.groq.com>
GOOGLE_CLIENT_ID=<from console.cloud.google.com>
GOOGLE_CLIENT_SECRET=<from console.cloud.google.com>
FRONTEND_URL=http://localhost:5173
# Optional:
JWT_SECRET=<random string for production>
```

## Key constraints

- **100% free**: Groq API key, HuggingFace embeddings (local), ChromaDB (local), yfinance, DuckDuckGo
- **No OpenAI, no Pinecone, no paid services**
- `backend/.env` must contain `GROQ_API_KEY` (gitignored)
- ChromaDB data lives in `backend/chromadb_storage/` (gitignored)
- PDF uploads: max 10 MB, `.pdf` only
- CORS: locked to `localhost:5173` and `localhost:4173`
- Google OAuth: authorized redirect URI must be `http://localhost:8000/api/auth/google/callback`

## RAG pipeline

1. POST `/api/ingest` with a PDF file
2. Text split into 500-char chunks (50 overlap)
3. Embedded with `sentence-transformers/all-MiniLM-L6-v2`
4. Stored in local ChromaDB (persistent)
5. Retriever returns top-3 chunks per query

## Session isolation

- All session queries filter by `user_id` (server-enforced)
- Sessions are per-user; one user cannot see another's sessions or messages
- Agent memory is keyed by `user_id:session_id`, rebuilt from DB on cache miss

## Deployment (Render)

- Backend: Web Service, persistent disk at `/app/chromadb_storage`, env `GROQ_API_KEY`
- Frontend: Static Site, build command `npm install && npm run build`, publish `dist`

## Tests

```bash
cd backend
.venv\Scripts\Activate; $env:PYTHONPATH = "$pwd"
python -m pytest tests/ -v
```

Uses FastAPI TestClient with per-test temp SQLite database. Tests verify behavior through public HTTP API, not implementation internals.
